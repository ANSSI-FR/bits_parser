# Copyright 2017 ANSSI. All Rights Reserved.
#
# Licensed under the MIT License (the "License");
# you may not use this file except in compliance with the License.
"""Known constants."""

FILE_HEADER =    '13F72BC84099124A9F1A3AAEBD894EEA'
QUEUE_HEADER =   '47445F00A9BDBA449851C47BB6C07ACE'
XFER_HEADER =    '36DA56776F515A43ACAC44A248FFF34D'
XFER_DELIMITER = '03000000'

WINVER = {
    0: 'NT 5.1',    # Windows 2003 / Windows XP
    1: 'NT 5.2',    # Windows 2003 R2 / Windows XP 64
    2: 'NT 6.0',    # Windows Vista / Windows 2008
    3: 'NT 6.1',    # Windows 7 / Windows 2008 R2
    4: 'NT 6.2',    # Windows 8 / Windows 2012
    5: 'NT 6.3',    # Windows 8.1 / Windows 2012 R2
}


# each version of BITS has its own job delimiter.
JOB_DELIMITERS = {
    1: '93362035A00C104A84F3B17E7B499CD7',
    2: '101370C83653B34183E581557F361B87',
    3: '8C93EA64030F6840B46FF97FE51D4DCD',
    4: 'B346ED3D3B10F944BC2FE8378BD31986',
}
