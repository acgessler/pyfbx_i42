FBX Binary File Encoding
========================

*August 2013, Alexander Gessler*

This is an incomplete specification for the binary FBX file format.
It has been tested with file versions starting 2011, but it should also work with earlier versions.

This document only describes the *encoding* of binary FBX files, not the interpretation of the data being encoded.
It should enable you to translate binary FBX files to ASCII text format (or an in-memory representation of it).


Text-Based File Structure
-------------------------

Knowledge of the text-based format is relevant for this document, so here is a quick writeup.
The core hierarchical building block (object) of a text-based FBX document is

    ::

        NodeType: SomeProperty0a, SomeProperty0b, ... , {

           NestedNodeType1 : SomeProperty1a, ...
           NestedNodeType2 : SomeProperty2a, ... , {
               ... Sub-scope
           }

           ...
        }

In other words, a document is essentially a nested list.
Each item has...

* A NodeType identifier (class name)
* A tuple of properties associated with it, the tuple elements are the usual primitive data types: ``float, integer, string`` etc.
* A list which contains data in the same format (recursively).

At global level, there is an "implicit dictionary" (i.e. the curly braces, the property list and the name are omitted)
with some standard nodes defined. Each of these standard items consists only of a nested list,
so a file might look like this

    ::

        FBXHeaderExtension: {...}
        GlobalSettings: {...}
        Documents: {...}
        Definitions: {...}
        Connections: {...}
        ...

Applications have to parse the contents of these in order to access FBX geometry.


Binary File Structure
---------------------

The first 27 bytes contain the header.

* Bytes ``0 - 20``: ``Kaydara FBX Binary  \x00`` (file-magic, with 2 spaces at the end, then a NULL terminator).
* Bytes ``21 - 22``: ``[0x1A, 0x00]`` (unknown but all observed files show these bytes).
* Bytes ``23 - 26``: unsigned int, the version number. *7300 for version 7.3 for example*.


Directly after this data, there is the top-level object record.
Unlike for the text file format, this is not omitted - a full object record *with empty name and empty property list* is written.

After that record (which recursively contains the entire file information) there is a footer with unknown contents.


Object Record Format
--------------------

A named object record has the following memory layout:

    ============    =========        ====
    Size (Bytes)    Data Type        Name
    ============    =========        ====
    4               Uint32           EndOffset
    4               Uint32           NumProperties
    4               Uint32           PropertyListLen
    1               Uint8t           NameLen
    NameLen         char             Name

    ?               ?                Property[n], for n in 0:PropertyListLen

    Optional
    ?               ?                NestedList
    13              uint8[]          NULL-record
    ============    =========        ====

Where...

* ``EndOffset`` is the distance from the beginning of the file to the end of the node record (i.e. the first byte of whatever comes next). This can be used to easily skip over unknown or not required records.
* ``NumProperties`` is the number of properties in the value tuple associated with the node. A nested list as last element is *not* counted as property.
* ``PropertyListLen`` is the length of the property list. This is the size required for storing ``NumProperties`` properties, which depends on the data type of the properties.
* ``NameLen`` is the length fo the object name, in characters. The only case where this is 0 seems to be the lists top-level.
* ``Name`` is the name of the object. There is no zero-termination.
* ``Property[n]`` is the ``n``'th property. For the format, see section *Property Record Format*. Properties are written sequentially and with no padding.
* ``NestedList`` is the nested list, presence of which is indicated by a ``NULL``-*record* at the very end.

Reading an object record up to and including the properties is straightforward.
To determine whether a nested list entry exists, check if there is bytes left until the ``EndOffset`` is reached.
If so, recursively read an object record directly following the last property. Behind that object record,
there is 13 zero bytes, which should then match up with the `EndOffset`.
(*Note*: it is not entirely clear why the NULL entry is required.
This strongly hints at some FBX sublety or format feature that not known to the authors of this document ....)


Property Record Format
----------------------

A property record has the following memory layout:

    ============    =========        ====
    Size (Bytes)    Data Type        Name
    ============    =========        ====
    1               char             TypeCode
    ?               ?                Data
    ============    =========        ====

where ``TypeCode`` can be one of the following character codes, which are ordered in groups that require similar handling.

**i)** Primitive Types

    * ``Y``: 2 byte signed Integer
    * ``C``: 1 bit boolean (1: ``true``, 0: ``false``) encoded as the LSB of a 1 Byte value.
    * ``I``: 4 byte signed Integer
    * ``F``: 4 byte single-precision IEEE 754 number
    * ``D``: 8 byte double-precision IEEE 754 number
    * ``L``: 8 byte signed Integer

    For primitive scalar types the ``Data`` in the record is exactly the binary representation of the value,
    in little-endian byte order.

**ii)** Array types

    * ``f``: Array of 4 byte single-precision IEEE 754 number
    * ``d``: Array of 8 byte double-precision IEEE 754 number
    * ``l``: Array of 8 byte signed Integer
    * ``i``: Array of 4 byte signed Integer

For array types (second group), ``Data`` is more complex:

    ============    =========        ====
    Size (Bytes)    Data Type        Name
    ============    =========        ====
    4               Uint32           ArrayLength
    4               Uint32           Encoding
    4               Uint32           CompressedLength
    ?               ?                Contents
    ============    =========        ====

If ``Encoding`` is 0, the ``Contents`` is just `ArrayLength` times the array data type. If ``Encoding`` is 1,
the ``Contents`` is a deflate/zip-compressed buffer of length ``CompressedLength`` bytes.
The buffer can for example be decoded using zlib.

**Values other than 0,1 for ``Encoding`` have not been observed**.

**iii)** Special types

    * ``S``: String
    * ``R``: raw binary data


Both of these have the following interpretation:

    ============    =========        ====
    Size (Bytes)    Data Type        Name
    ============    =========        ====
    4               Uint32           Length
    Length          byte/char        Data
    ============    =========        ====

The string is not zero-terminated, and may well contain ``\0`` characters (this is actually used in some FBX properties).


**iv)** Unknown types

    * ``b``: ???
