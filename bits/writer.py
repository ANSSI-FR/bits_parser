# Copyright 2017 ANSSI. All Rights Reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
"""CSV writer."""
import csv


DEFAULT_VALUES = (
    ('job_id', None),
    ('name', None),
    ('desc', None),
    ('type', None),
    ('priority', None),
    ('sid', None),
    ('state', None),
    ('cmd', None),
    ('args', None),
    ('file_count', 0),
    ('file_id', 0),
    ('dest_fn', None),
    ('src_fn', None),
    ('tmp_fn', None),
    ('download_size', -1),
    ('transfer_size', -1),
    ('drive', None),
    ('vol_guid', None),
    ('ctime', None),
    ('mtime', None),
    ('other_time0', None),
    ('other_time1', None),
    ('other_time2', None),
    ('carved', False)
)


def flattener(job):

    def _f(index, file):
        rv = {k: file.get(k, job.get(k, v))  for k, v in DEFAULT_VALUES}
        rv['file_id'] = index
        return rv

    files = job.get('files', [])

    if files:
        return [_f(index, f) for index, f in enumerate(files)]

    return [_f(0, {})]


def write_csv(filename, records):
    """Write records to a CSV file."""

    with filename.open('w') as csvfile:
        writer = csv.DictWriter(csvfile,
                                fieldnames=[k for k, _ in DEFAULT_VALUES])
        writer.writeheader()
        for r in records:
            for sub_r in flattener(r):
                writer.writerow(sub_r)
