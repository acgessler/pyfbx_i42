pyfbx_i42
=========

Currently this project contains ``pyfbx/parse_bin.py``, a simple but functional parser for binary FBX data, which can load in the FBX hierarchy.

It doesn't (yet) contain utility functions for dealing with the data.

What Works
----------
- tested FBX files from 2006 - 2012 _(parsing data seems not to depend on exact versions)_
- all known datatypes (float/int arrays, loading binary data, strings etc).
- zlib compression

What Doesn't Work
-----------------
- ASCII FBX
- todo...
