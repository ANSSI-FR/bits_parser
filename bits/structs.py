# Copyright 2017 ANSSI. All Rights Reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
"""Data structures.

Multiple data structures are available. Those structures are defined to
facilitate parsing and carving but returns an object or list of objects
containing all the following fields:

header
job_count
jobs ->
    type                    Job type (enumeration).
    priority                Job priority (enumeration).
    state                   State of the job (enumeration).
    job_id                  UUID of the job.
    name                    Name of the job.
    desc                    Description string of the job.
    cmd                     Command executed when the job is done.
    args                    Arguments of the command.
    sid                     Owner of the job.
    flags
    access_token
    file_count              Count of transferred files of the job.
    files ->
        dest_fn             Destination file path of a file.
        src_fn              Source URL.
        tmp_fn              Temporary file path of a file.
        download_size       The count of donwloaded bytes.
        transfer_size
        drive               Destination drive.
        vol_guid            Volume GUID of the drive.
    error_count
    errors ->
        code
        stat1
        stat2
        stat3
        stat4
    transient_error_count
    retry_delay
    timeout
    ctime
    mtime
    other_time0
    other_time1
    other_time2


"""

# available fields



from bits.const import FILE_HEADER, QUEUE_HEADER, XFER_HEADER

from bits.helpers.fields import DelimitedField, PascalUtf16, FileTime, UUID
from construct import Struct, Array, Enum, Const, GreedyBytes, Int64ul, \
    Int32ul, Bytes, Byte, Pass, Padding, Embedded, Tell, Seek, this


QUEUE = Struct(
    'header'        / DelimitedField(bytes.fromhex(FILE_HEADER)),
    Const(bytes.fromhex(FILE_HEADER)),
    Const(bytes.fromhex(QUEUE_HEADER)),
    'job_count'     / Int32ul,
    'jobs'          / DelimitedField(bytes.fromhex(QUEUE_HEADER)),
    Const(bytes.fromhex(QUEUE_HEADER)),
    'unknown'       / DelimitedField(bytes.fromhex(FILE_HEADER)),
    Const(bytes.fromhex(FILE_HEADER)),
    'remains'       / GreedyBytes,
)


# CONTROL : job control informations
CONTROL_PART_0 = Struct(
    'type'          / Enum(Int32ul, default=Pass,
        download=0,
        upload=1,
        upload_reply=2),
    'priority'      / Enum(Int32ul, default=Pass,
        foreground=0,
        high=1,
        normal=2,
        low=3),
    'state'         / Enum(Int32ul, default=Pass,
        queued=0,
        connecting=1,
        transferring=2,
        suspended=3,
        error=4,
        transient_error=5,
        transferred=6,
        acknowleged=7,
        cancelled=8),
    Int32ul,
    'job_id'        / UUID(Bytes(16)),
)


CONTROL_PART_1 = Struct(
    'sid'           / PascalUtf16(Int32ul),
    'flags'         / Enum(Int32ul, default=Pass,
        BG_NOTIFY_JOB_TRANSFERRED=1,
        BG_NOTIFY_JOB_ERROR=2,
        BG_NOTIFY_JOB_TRANSFERRED_BG_NOTIFY_JOB_ERROR=3,
        BG_NOTIFY_DISABLE=4,
        BG_NOTIFY_JOB_TRANSFERRED_BG_NOTIFY_DISABLE=5,
        BG_NOTIFY_JOB_ERROR_BG_NOTIFY_DISABLE=6,
        BG_NOTIFY_JOB_TRANSFERRED_BG_NOTIFY_JOB_ERROR_BG_NOTIFY_DISABLE=7,
        BG_NOTIFY_JOB_MODIFICATION=8,
        BG_NOTIFY_FILE_TRANSFERRED=16),
)


CONTROL = Struct(
    Embedded(CONTROL_PART_0),
    'name'          / PascalUtf16(Int32ul),
    'desc'          / PascalUtf16(Int32ul),
    'cmd'           / PascalUtf16(Int32ul),
    'args'          / PascalUtf16(Int32ul),
    Embedded(CONTROL_PART_1),
    'access_token'  / DelimitedField(bytes.fromhex(XFER_HEADER)),
)


# XFER : file transfer informations

FILE_PART_0 = Struct(
    'download_size' / Int64ul,
    'transfer_size' / Int64ul,
    Byte,
    'drive'         / PascalUtf16(Int32ul),
    'vol_guid'      / PascalUtf16(Int32ul),
    'offset'        / Tell,                     # required by carving
)


FILE = Struct(
    DelimitedField(b':'),
    Seek(-6, whence=1),
    'dest_fn'       / PascalUtf16(Int32ul),
    'src_fn'        / PascalUtf16(Int32ul),
    'tmp_fn'        / PascalUtf16(Int32ul),     # always ends with .tmp
    Embedded(FILE_PART_0),
)


ERROR = Struct(
     'code'         / Int64ul,
     'stat1'        / Int32ul,
     'stat2'        / Int32ul,
     'stat3'        / Int32ul,
     'stat4'        / Int32ul,
     Byte
)


METADATA = Struct(
    'error_count'     / Int32ul,
    'errors'        / Array(this.error_count, ERROR),
    'transient_error_count' / Int32ul,
    'retry_delay'   / Int32ul,
    'timeout'       / Int32ul,
    'ctime'         / FileTime(Int64ul),
    'mtime'         / FileTime(Int64ul),
    'other_time0'   / FileTime(Int64ul),
    Padding(14),
    'other_time1'   / FileTime(Int64ul),
    'other_time2'   / FileTime(Int64ul),
)


JOB = Struct(
    Embedded(CONTROL),
    Const(bytes.fromhex(XFER_HEADER)),
    'file_count'    / Int32ul,
    'files'         / DelimitedField(bytes.fromhex(XFER_HEADER)),
    Const(bytes.fromhex(XFER_HEADER)),
    Embedded(METADATA),
)
