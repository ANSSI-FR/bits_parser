# Copyright 2017 ANSSI. All Rights Reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
"""Implements a features to carve ill-formatted data."""

import logging
import construct.core

from bits.const import FILE_HEADER, QUEUE_HEADER, XFER_HEADER
from bits.helpers.fields import PascalUtf16
from bits.structs import METADATA, \
                         FILE, FILE_PART_0, \
                         CONTROL_PART_0, CONTROL_PART_1


logger = logging.getLogger(__name__)


def carve_queues(data):
    """Carve binary queue fragments."""
    delimiter = bytes.fromhex(QUEUE_HEADER)
    queues = [q for q in data.split(delimiter) if q.strip(b'\x00')]
    logger.debug('queues: %d non-empty candidates' % len(queues))
    return queues


def carve_jobs(data, delimiter):
    """Carve binary job fragments."""
    if delimiter is None:
        jobs = [data]
    else:
        jobs = [j for j in data.split(delimiter) if j.strip(b'\x00')]

    logger.debug('jobs: %d non-empty candidates' % len(jobs))
    return jobs


def rcarve_pascal_utf16(data, *fields):
    """Search for utf16 fields in bytes."""
    rv = {}
    remaining_data = None

    for field in fields:
        valid_string = None

        for i in range(len(data) - 4, -1, -2):
            try:
                valid_string = PascalUtf16().parse(data[i:])
            except construct.core.ConstructError:
                pass    # invalid data
            else:
                rv[field] = valid_string
                data = data[:i]
                remaining_data = data
                break

        if valid_string is None:
            remaining_data = None
            # UGLY: extraction tentative of the remaining bytes
            for j in range(2, len(data), 2):
                try:
                    res = data[-j:].replace(b'\x00', b'').decode()
                except UnicodeDecodeError:
                    break
                else:
                    if res:
                        rv[field] = res
            break       # no more data available

    return rv, remaining_data


def files_deep_carving(data, pivot_offset):
    """Carve partial file information from bytes."""
    carved_files = []

    # the data is split in two parts on the pivot offset to separate stable
    # data from truncated data.
    partial = data[:pivot_offset]
    remains = data[pivot_offset:]

    # process the first bytes for relevant data
    rv, _ = rcarve_pascal_utf16(partial, 'tmp_fn', 'src_fn', 'dest_fn')
    if rv:
        carved_files.append(rv)
    else:
        return carved_files

    # update file #0 informations
    try:
        rv = FILE_PART_0.parse(remains)
    except construct.core.ConstructError:
        return carved_files
    else:
        carved_files[0].update(rv)
        remains = remains[rv.offset:]

    # insert files #1 and others if any
    while remains:
        try:
            new_file = FILE.parse(remains)
        except construct.core.ConstructError:
            break
        else:
            carved_files.append(dict(new_file))
            remains = remains[new_file.offset:]

    return carved_files


def control_deep_carving(data, pivot_offset):
    """Carve partial file information from bytes."""
    # the data is split in two parts on the pivot offset to separate stable
    # data from truncated data.
    partial = data[:pivot_offset]
    remains = data[pivot_offset:]

    rv, sub_data = rcarve_pascal_utf16(partial, 'args', 'cmd', 'desc', 'name')
    if sub_data and len(sub_data) == 32:
        try:
            rv.update(CONTROL_PART_0.parse(sub_data))
        except construct.core.ConstructError:
            pass

    try:
        rv.update(CONTROL_PART_1.parse(remains))
    except construct.core.ConstructError as e:
        pass

    return rv


def deep_carving(data):
    """Try to carve bytes for recognizable data."""

    rv = {}

    if data.startswith(bytes.fromhex(FILE_HEADER)):
        data = data[16:]

    # Search for an SID (always starts with S-1- in utf16)
    pattern = b'S\x00-\x001\x00-\x00'
    sid_index = data.find(pattern)

    pattern = b'.\x00t\x00m\x00p\x00'
    bittmp_index = data.find(pattern)

    if sid_index > -1:
        rv.update(control_deep_carving(data, sid_index - 4))

    elif bittmp_index > -1:
        files = files_deep_carving(data, bittmp_index + 10)
        if files:
            rv['file_count'] = len(files)
            rv['files'] = files

    return rv


def carve_sections(data):
    """Carve data has potential section in a job."""
    # A valid job is comprised of 2 to 3 sections:
    #
    # - description and controls
    # - file transfers (optional)
    # - metadata
    #
    # When carving data, most of the time, the first available section is
    # partially overwritten making it difficult to retrieve relevant data.
    # The last available one is always the metadata section.
    delimiter = bytes.fromhex(XFER_HEADER)
    sections = [s for s in data.split(delimiter) if s.strip(b'\x00')]

    lost_bytes = 0

    rv = {}

    for section in reversed(sections):

        logger.debug('searching for file transfers ...')
        files = []

        file_count = int.from_bytes(section[:4], byteorder='little')

        if file_count * 37 < len(section):
            logger.debug('trying to carve %d transfers' % file_count)
            offset = 4
            while file_count > len(files) and section[offset:]:
                try:
                    recfile = FILE.parse(section[offset:])
                    if any(v for k, v in recfile.items() if k != 'offset'):
                        files.append(recfile)

                    # remove invalid transfer_size
                    if recfile['transfer_size'] == 0xFFFFFFFFFFFFFFFF:
                        recfile['transfer_size'] = ''

                except (UnicodeDecodeError, construct.core.ConstructError):
                    offset += 1
                    if offset == 16:   # don't waste time on irrelevant data.
                        break          # 16 is an arbitrary high value
                else:
                    if files:
                        logger.debug('new transfer found!')
                        offset += recfile.offset  # the offset is now after the
                                                  # newly carved file transfer

        if files:
            rv['file_count'] = file_count
            rv['files'] = files
            continue
        else:
            logger.debug('unrecognized transfer section')

        try:
            rv.update(METADATA.parse(section))
        except (OverflowError, construct.core.ConstructError):
            logger.debug('unrecognized metadata section')
        else:
            continue

        logger.debug('trying to deep carve %d bytes' % (len(section)))
        remains = deep_carving(section)
        if remains:
            rv.update(remains)

        else:
            lost_bytes += len(section)

    if lost_bytes:
        logger.debug('%d bytes of unknown data' % lost_bytes)

    return rv, lost_bytes
