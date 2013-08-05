pyfbx_i42
=========

Currently this project contains ``pyfbx/parse_bin.py``,
a simple but functional parser for binary FBX data, which can load in the FBX hierarchy.

It doesn't (yet) contain utility functions for dealing with the data.

This script is based on assimp's ``FBXBinaryTokenizer.cpp``

What Works
----------
- tested FBX files from 2006 - 2012
  *(parsing data seems not to depend on exact versions)*
- all known datatypes (float/int arrays, loading binary data, strings etc).
- zlib compression

What Doesn't Work
-----------------
- ASCII FBX
- The data type 'b',
  *(aparently nobody knows what this is for, need to investigate)*.


Examples
--------

Currently there is a simple example script called ``fbx2json.py``
this standalone Python script will write a ``JSON`` file for each ``FBX`` passed,
Even though its intended mainly as an example it may prove useful in some situations.
