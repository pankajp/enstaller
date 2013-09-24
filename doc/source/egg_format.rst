Our egg format is an extension of the existing setuptools's egg.

A few notations:

    - $PREFIX: is understood as the prefix of the current python. In a standard
      install, $PREFIX/bin/python will contain python on unix,
      $PREFIX/python.exe on windows.
    - $BINDIR: where 'binaries' are installed. Generally $PREFIX/bin on unix,
      $PREFIX\\Scripts on windows.
    - $METADIR: package-specific directory where files/metadata get installed.
      Generally $PREFIX/EGG-INFO/$package_name

EGG-INFO subdirectory
=====================

This subdirectory contains all the metadata needed by egginst to install an egg
properly. It contains various text files with ad-hoc, poorly specified format.

EGG-INFO/inst
-------------

files_to_install.txt
~~~~~~~~~~~~~~~~~~~~

This file is used to define so-called proxies (a clumsy way to emulate
softlinks on windows) and support softlinks on non-windows platform. The file
defines one entry per line, and each entry is a space separated set of two
items.

On linux and os x, each entry looks as follows::

     EGG-INFO/usr/lib/libzmq.so                         libzmq.so.0.0.0

This defines a link join(prefix, 'lib/libzmq.so') to libzmq.so.0.0.0. More
precisely:

    - the left part is used to define the link name, the right part the target
      of the link.
    - the actual link name will be a join of the prefix + the part that comes
      after EGG-INFO/usr.

Entries may also look as follows::

     EGG-INFO/usr/bin/xslt-config                       False

This does not define a link to False, but instead tells egginst to ignore this
entry. Don't ask me why the entry is there in the first place...

A third format only encountered on windows' eggs::

    {TARGET}  {ACTION}

where {TARGET} must be in the zip archive, and where {ACTION} may be one of the
following:

    - PROXY: a proxy to the left part is created. A proxy is a set of two
      files, both written in the $BINDIR

        - one small exe which is a copy of the setuptools' cli.exe, renamed to
          basename({TARGET}).
        - another file {TARGET_NO_EXTENSION}-script.py where
          TARGET_NO_EXTENSION = basename(splitext({TARGET}))

    - Anything else: understood as a directory. In that case, {TARGET} will be
      copied into $ROOT\\{ACTION}\\basename({TARGET})

A PROXY example::

    EGG-INFO/usr/bin/ar.exe  PROXY

Egginst will create the following::

    # A copy of cli.exe
    $BINDIR\\ar.exe
    # the python script called by $BINDIR\\ar.exe, itself calling
    # $METADIR\\usr\\bin\\ar.exe
    $BINDIR\\ar-script.py

A non-PROXY example::

    EGG-INFO/usr/bin/ar.exe  EGG-INFO/mingw/usr/i686-w64-mingw32/bin

Egginst will create the following::
   
    # A copy of EGG-INFO/usr/bin/ar.exe
    $METADIR\\usr\\i686-w64-mingw32\\bin.ar.exe
