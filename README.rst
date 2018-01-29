===========
bits_parser
===========


Extract BITS jobs from QMGR queue and store them as CSV records.

This topic has been presented during a talk at the French conference `CORI&IN 2018 <https://www.cecyf.fr/activites/recherche-et-developpement/coriin-2018/>`_


Installation
============

If you want to run the latest version of ``bits_parser`` you can install it
from PyPI by running the following command:

  .. code:: bash

    pip install bits_parser


To install it from the sources:

  .. code:: bash

    python setup.py install


Usage
=====

QMGR queues are usually *.dat* files located in the folder
``%%ALLUSERSPROFILE%%\Microsoft\Network\Downloader`` on a Windows system.

Once those files have been located (*e.g.* ``qmgr0.dat`` and ``qmgr1.dat``) you
can run `bits_parser` by issuing the following command:

  .. code:: bash

    bits_parser qmgr0.dat

`bits_parser` also supports full-disk analysis but the process is longer and
the results are dirtier (some data from adjacent data clusters can leak in the
result). This mode is enable with the switch `-i`:

  .. code:: bash

    bits_parser -i image.bin

The disk mode works by looking for expected bit sequences (markers) and
collecting surrounding data. The amount of surrounding data (the radiance) is
settable and defaulted to 2048 kB:

  .. code:: bash

    bits_parser -i --radiance=4096 image.bin

Increasing the radiance could help to retrieve more data but the default value
is normally enough.

When the processing is finished, the result is csv-formatted and then displayed
on the standard output. The output can be written to a file with `-o`:

  .. code:: bash

    bits_parser -o jobs.csv qmgr0.dat

Use `--help` to display all options options of ``bits_parser``.


Related works
=============

`Finding your naughty BITS <https://www.dfrws.org/sites/default/files/session-files/pres-finding_your_naughty_bits.pdf>`_ [DFRWS USA 2015, Matthew Geiger]

`BITSInject <https://github.com/SafeBreach-Labs/BITSInject>`_ [DEFCON 2017, Dor Azouri]
