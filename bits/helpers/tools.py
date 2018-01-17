# Copyright 2017 ANSSI. All Rights Reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
"""Some helpers."""


def tcid(obj, key, default=None):
    """Search a dict by its value."""
    d = {v: k for k, v in obj.items()}
    return d.get(key, default)


def btcid(obj, key, default=None):
    """Search a binary value in a dict."""
    if hasattr(key, 'hex'):
        key = key.hex().upper()
    return tcid(obj, key, default)
