# Copyright 2017 ANSSI. All Rights Reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
"""Bits object."""
import logging
import construct.core

from pathlib import Path

from bits.structs import QUEUE, JOB, FILE
from bits.const import JOB_DELIMITERS, XFER_DELIMITER
from bits.carver import carve_queues, carve_jobs, carve_sections

logger = logging.getLogger(__name__)


class Bits:
    """
    An interface to store data and apply different strategies to extract job
    details from legitimate or (partially) corrupted data.

    Args:
        delimiter: force the job delimiter.
    """

    def __init__(self, delimiter=None):

        self._raw_data = bytes()
        self._bits_data = bytes()
        self.delimiter = delimiter

    @classmethod
    def load_file(cls, fp):
        """Create a Bits instance and load data from a QMGR file.

        This method is a simple helper to append the content of a file and
        automatically call `guess_info()`.

        Args:
            fp: file path to a QMGR file.
        """
        logger.info('Processing BITS queue %s' % fp)

        rv = cls()

        path = Path(fp).resolve()
        with path.open('rb') as f:
            data = f.read()
        try:
            content = QUEUE.parse(data)
            rv.append_data(content.jobs, raw=False)
            rv.append_data(content.remains, raw=True)
            if content.job_count:
                logger.info('%s legitimate job(s) detected' % content.job_count)

        except construct.core.ConstructError as e:
            logger.warning('incoherent data, carving mode only.')
            rv.append_data(data, raw=True)

        rv.guess_info()
        return rv

    def append_data(self, data, raw=True):
        """Append data to analyze.

        Args:
            data: bytes to append.
            raw: true when appending unparsed raw data.
        """
        data = data.strip(b'\x00')  # strip unwanted zeroes
        logger.debug('%d bytes loaded (raw=%s)' % (len(data), raw))
        if raw:
            self._raw_data += data
        else:
            self._bits_data += data

    def guess_info(self):
        """Try to guess information from available data."""
        # select as candidate the known delimiter with the most occurences
        data = self._bits_data + self._raw_data

        if not self.delimiter:
            count, candidate = max(
                (data.count(bytes.fromhex(d)), bytes.fromhex(d))
                for d in JOB_DELIMITERS.values()
            )

            self.delimiter = candidate if count else None

        # log
        if self.delimiter is not None:
            logger.info('Job delimiter is %s' % self.delimiter.hex().upper())
        else:
            logger.warning('Job delimiter is undefined')

    def parse(self):
        """Parse and yield job data in BITS data structures.

        This method is based on expected data structures in a BITS queue and
        works on well-formatted data.

        Yields: jobs.
        """
        xfer_delimiter = bytes.fromhex(XFER_DELIMITER)

        if self._bits_data and self.delimiter:
            logger.debug('Analysis of %d bytes' % len(self._bits_data))
            chunks = (j for j in self._bits_data.split(self.delimiter) if j)
            for data in chunks:

                try:
                    job = dict(JOB.parse(data))
                except construct.core.ConstructError as e:
                    logger.debug('%d bytes of unknown data' % len(data))
                    continue

                xfers = (x for x in job.pop('files').split(xfer_delimiter))
                job['files'] = []

                for f in xfers:
                    try:
                        job['files'].append(FILE.parse(f))
                    except construct.core.ConstructError as e:
                        logger.debug('%d bytes of unknown data' % len(f))

                if job['file_count'] != len(job['files']):
                    err_msg = 'Invalid transfer count: %d found, %d expected.'
                    logger.warning(err_msg % (len(job['files']),
                                              job['file_count']))

                yield job
        else:
            logger.info('No legitimate data found.')

    def carve(self, raw=True):
        """Search and yield job data in raw bytes by carving it.

        This method uses multiple functions to retrieve fragments of queues,
        jobs or internal sections and consolidate this all together.

        Data with no relevant informations (empty or completely erroneous) are
        dropped.

        Args:
            raw: carve raw bytes (default: True)

        Yields: jobs or partial jobs.
        """
        data = self._raw_data if raw else self._bits_data
        logger.debug('Analysis of %d bytes' % len(data))

        for b_queue in carve_queues(data):
            for b_job in carve_jobs(b_queue, self.delimiter):
                    job, lost_bytes = carve_sections(b_job)

                    # no job data
                    if not job:
                        continue

                    # no value found
                    if not any(job.values()):
                        continue

                    # no file information
                    if job.get('file_count', 0) == 1 and \
                       not any(job['files'][0].values()):
                        continue

                    job['carved'] = True    # indicate the job was carved
                    yield job

    def __iter__(self):

        yield from self.parse()
        yield from self.carve()
