# Copyright 2017 ANSSI. All Rights Reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
"""Disk analysis features."""
import logging


from pathlib import Path

logger = logging.getLogger(__name__)


def _radiance_read(f, start_offset, pattern, radiance):

    # Radiance algorithm :
    #
    #      @0             @1             @2
    #  <--------[pattern]----[pattern]-------->
    #
    # @0: predecessing bytes not containing the pattern.
    # @1: intermediate data not containing the pattern with a size
    #    inferior at the size of the radiance.
    # @2: following bytes not containing the pattern.
    #
    # size(@0) == size(@2) == size(radiance)
    # size(@1) < size(radiance)

    # get predecessing bytes
    f.seek(start_offset)
    rv = f.read((radiance * 1024) + len(pattern))   # read @0 + 1st pattern

    while True:
        rv_tmp = f.read(radiance * 1024)

        if len(rv_tmp) < radiance * 1024:               # end of the file
            return rv + rv_tmp

        local_offset = rv_tmp.rfind(pattern)
        if local_offset >= 0:                           # intermediate pattern
            rv += rv_tmp[:local_offset + len(pattern)]
            f.seek(f.tell() - (radiance * 1024) + local_offset + len(pattern))
        else:
            return rv + rv_tmp                          # pattern not found


def sample_disk(img_fp, pattern, radiance=4096):
    """Extract interesting disk image samples containing a specific pattern.

    img_fp: disk image file path.
    pattern: bytes or hex-string of the specific pattern.
    radiance: size in kB of collected data not containing the pattern
        surrounding the matched pattern.

    Yields: disk samples (bytes)
    """

    img_fp = Path(img_fp).resolve()

    logger.info('disk analysis of %s', img_fp)
    logger.info('search for pattern 0x%s R:%d', pattern, radiance)

    # ensure pattern is bytes
    if isinstance(pattern, str):
        pattern = bytes.fromhex(pattern)

    buf = [bytearray(512), bytearray(512)]  # dual buffer

    with img_fp.open('rb') as f:
        while f.readinto(buf[1]):
            data = b''.join(buf)

            local_offset = data.find(pattern, 511-len(pattern))
            if local_offset >= 0:

                # absolute offset of the pattern in the file.
                abs_offset = f.tell() - 1024 + local_offset

                # radiance start offset
                start_offset = max(0, abs_offset - (radiance * 1024))
                yield _radiance_read(f, start_offset, pattern, radiance)

            buf.reverse()   # permute the list

    logger.info('disk analysis complete')
