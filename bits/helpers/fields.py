# Copyright 2017 ANSSI. All Rights Reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
"""Some helpers."""

from uuid import UUID as _UUID
from datetime import datetime, timedelta
from construct import Adapter, Sequence, RepeatUntil, Byte, Bytes, Computed, \
                      Int32ul, Seek, this, Container


class _StripDelimiter(Adapter):

    def _decode(self, obj, context, path):
        return bytes(obj[1])


class _Utf16(Adapter):

    def _decode(self, obj, context, path):
        try:
            return obj[1].decode('utf16').strip('\x00')
        except UnicodeDecodeError:
            # TODO: improve that
            return 'unreadable data'

class DateTime(Adapter):

    def _decode(self, obj, context, path):
        return datetime.fromtimestamp(obj)


class UUID(Adapter):

    def _decode(self, obj, context, path):
        return str(_UUID(bytes_le=obj))


class FileTime(Adapter):

    def _decode(self, obj, context, path):
        return datetime(1601, 1, 1) + timedelta(microseconds=(obj / 10))

def DelimitedField(stop):

    return _StripDelimiter(Sequence(
        'with_delimiter' / RepeatUntil(
            lambda x, lst, ctx: lst[-len(stop):] == [int(c) for c in stop],
            Byte
        ),
        'stripped' / Computed(this['with_delimiter'][:-len(stop)]),
        Seek(-len(stop), whence=1)
    ))


def PascalUtf16(size_type=Int32ul):
    """Parse a length-defined string in UTF-16."""

    return _Utf16(Sequence(
        'size_type' / size_type,
        Bytes(this['size_type'] * 2),
    ))


class FlattenStruct(Adapter):
    
    def _decode(self, obj, context, path):
        result = Container()
        for key, value in obj.items():
            if type(value) is Container:
                result.update(value)
            else:
                result[key] = value
        
        return result
