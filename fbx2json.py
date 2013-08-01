#!/usr/bin/env python3
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# Script copyright (C) 2013 Campbell Barton

from pyfbx import parse_bin
from pyfbx import data_types
import json
import array


def fbx2json_property_as_string(prop, prop_type):
    if prop_type == data_types.STRING:
        prop_str = prop.decode('utf-8')
        prop_str = prop_str.replace('\x00\x01', '::')
        return json.dumps(prop_str)
    else:
        prop_py_type = type(prop)
        if prop_py_type == bytes:
            return json.dumps(repr(prop)[2:-1])
        elif prop_py_type == bool:
            return json.dumps(prop)
        elif prop_py_type == array.array:
            return repr(list(prop))

    return repr(prop)


def fbx2json_properties_as_string(fbx_elem):
    return ", ".join(fbx2json_property_as_string(*prop_item)
                     for prop_item in zip(fbx_elem.props,
                                          fbx_elem.props_type))


def fbx2json_recurse(fw, fbx_elem, ident, is_last):
    fbx_elem_id = fbx_elem.id.decode('utf-8')
    fw(ident + '["%s", ' % fbx_elem_id)
    fw('[%s], ' % fbx2json_properties_as_string(fbx_elem))

    fw('[')
    if fbx_elem.elems:
        fw('\n')
        ident_sub = ident + "    "
        for fbx_elem_sub in fbx_elem.elems:
            fbx2json_recurse(fw, fbx_elem_sub, ident_sub,
                             fbx_elem_sub is fbx_elem.elems[-1])
    fw(']')

    fw(']%s' % ('' if is_last else ',\n'))


def fbx2json(fn):
    import os

    fn_json = os.path.splitext(fn)[0] + ".json"
    print("Writing: %r..." % fn_json)

    fbx_root_elem = parse_bin.parse(fn, use_namedtuple=True)
    with open(fn_json, 'w', encoding="ascii", errors='xmlcharrefreplace') as f:
        fw = f.write
        fw('[\n')
        ident_sub = "    "
        for fbx_elem_sub in fbx_root_elem.elems:
            fbx2json_recurse(f.write, fbx_elem_sub, ident_sub,
                             fbx_elem_sub is fbx_root_elem.elems[-1])
        fw(']\n')


def main():
    import sys

    for arg in sys.argv[1:]:
        try:
            fbx2json(arg)
        except:
            print("Failed to convert %r, error:" % arg)

            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
