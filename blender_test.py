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

# Script copyright (C) Campbell Barton

# FBX 7.1.0 loader for blender

import os
use_cycles = False

try:
    import bpy
except:
    bpy = None
print("starting: %s" % ("in blender" if bpy else "alone"))
from pyfbx import parse_bin, data_types

# /src/blender/blender.bin --background --env-system-scripts /src/blender/release/scripts --enable-autoexec --python /src/pyfbx_i42/blender_test.py

# fn = "/root/untitled_bin.fbx"

# -----
# Utils

def elem_find_first(elem, id_search):
    for fbx_item in elem.elems:
        if fbx_item.id == id_search:
            return fbx_item

def elem_find_first_string(elem, id_search):
    fbx_item = elem_find_first(elem, id_search)
    if fbx_item is not None:
        assert(len(fbx_item.props) == 1)
        assert(fbx_item.props_type[0] == data_types.STRING)
        return fbx_item.props[0].decode('utf-8')
    return None


def elem_find_first_bytes(elem, id_search, decode=True):
    fbx_item = elem_find_first(elem, id_search)
    if fbx_item is not None:
        assert(len(fbx_item.props) == 1)
        assert(fbx_item.props_type[0] == data_types.STRING)
        return fbx_item.props[0]
    return None


def elem_repr(elem):
    return "%s: props[%d=%r], elems=(%r)" % (
           elem.id,
           len(elem.props),
           ", ".join([repr(p) for p in elem.props]),
           # elem.props_type,
           b", ".join([e.id for e in elem.elems])
           )


def elem_split_name_class(elem):
    """ Return 
    """
    assert(elem.props_type[-2] == data_types.STRING)
    elem_name, elem_class = elem.props[-2].split(b'\x00\x01')
    return elem_name, elem_class

def elem_uuid(elem):
    assert(elem.props_type[0] == data_types.INT64)
    return elem.props[0]
    


def elem_prop_first(elem):
    return elem.props[0] if (elem is not None) and elem.props else None


# ----
# Support for
# Properties70: { ... P:
def elem_props_find_first(elem, elem_prop_id):
    for subelem in elem.elems:
        assert(subelem.id == b'P')
        if subelem.props[0] == elem_prop_id:
            return subelem
    return None

def elem_props_get_color_rgb(elem, elem_prop_id, default=None):
    elem_prop = elem_props_find_first(elem, elem_prop_id)
    if elem_prop is not None:
        assert(elem_prop.props[0] == elem_prop_id)
        if elem_prop.props[1] == b'Color':
            # FBX version 7300
            assert(elem_prop.props[1] == b'Color')
            assert(elem_prop.props[2] == b'')
            assert(elem_prop.props[3] == b'A')
        else:
            assert(elem_prop.props[1] == b'ColorRGB')
            assert(elem_prop.props[2] == b'Color')
            #print(elem_prop.props_type[4:7])
        assert(elem_prop.props_type[4:7] == bytes((data_types.FLOAT64,)) * 3)
        return elem_prop.props[4:7]
    return default

def elem_props_get_number(elem, elem_prop_id, default=None):
    elem_prop = elem_props_find_first(elem, elem_prop_id)
    if elem_prop is not None:
        assert(elem_prop.props[0] == elem_prop_id)
        assert(elem_prop.props[1] == b'double')
        assert(elem_prop.props[2] == b'Number')
        assert(elem_prop.props_type[4] == data_types.FLOAT64) # we could allow other number types
        return elem_prop.props[4]
    return default


# -------
# Blender

# Tables: (FBX_byte_id -> [FBX_data, None or Blender_datablock])
fbx_table_object = {}

# ----
# Mesh

def blen_read_geom_layerinfo(fbx_layer):
    return (
        elem_find_first_string(fbx_layer, b'Name'),
        elem_find_first_bytes(fbx_layer, b'MappingInformationType'),
        elem_find_first_bytes(fbx_layer, b'ReferenceInformationType'),
        )


def blen_read_geom_uv(fbx_obj, me):

    for uvlayer_id in (b'LayerElementUV',):
        fbx_uvlayer = elem_find_first(fbx_obj, uvlayer_id)
        
        if fbx_uvlayer is None:
            continue

        # all should be valid
        (fbx_uvlayer_name,
         fbx_uvlayer_mapping,
         fbx_uvlayer_ref,
         ) = blen_read_geom_layerinfo(fbx_uvlayer)

        # print(fbx_uvlayer_name, fbx_uvlayer_mapping, fbx_uvlayer_ref)

        fbx_layer_data = elem_prop_first(elem_find_first(fbx_uvlayer, b'UV'))
        fbx_layer_index = elem_prop_first(elem_find_first(fbx_uvlayer, b'UVIndex'))

        # TODO, generic mappuing apply function
        if fbx_uvlayer_mapping == b'ByPolygonVertex':
            if fbx_uvlayer_ref == b'IndexToDirect':
                # TODO, more generic support for mapping types
                uv_tex = me.uv_textures.new(name=fbx_uvlayer_name)
                uv_lay = me.uv_layers[fbx_uvlayer_name]
                uv_data = [luv.uv for luv in uv_lay.data]

                for i, j in enumerate(fbx_layer_index):
                    uv_data[i][:] = fbx_layer_data[(j * 2) : (j * 2) + 2]
            else:
                print("warning uv layer ref type unsupported:", fbx_uvlayer_ref)
        else:
            print("warning uv layer mapping type unsupported:", fbx_uvlayer_mapping)

        # print("AAA", fbx_uvlayer)
        # print("AAA", fbx_layer_data)


def blen_read_geom(fbx_obj):
    elem_name, elem_class = elem_split_name_class(fbx_obj)
    assert(elem_class == b'Geometry')
    elem_name_utf8 = elem_name.decode('utf-8')

    fbx_verts = elem_prop_first(elem_find_first(fbx_obj, b'Vertices'))
    fbx_polys = elem_prop_first(elem_find_first(fbx_obj, b'PolygonVertexIndex'))
    # TODO
    # fbx_edges = elem_prop_first(elem_find_first(fbx_obj, b'Edges'))

    # print(fbx_obj.props)
    # print(fbx_verts)
    # print(fbx_polys)
    me = bpy.data.meshes.new(name=elem_name_utf8)
    me.vertices.add(len(fbx_verts) // 3)
    me.vertices.foreach_set("co", fbx_verts)

    me.loops.add(len(fbx_polys))

    #poly_loops = []  # pairs (loop_start, loop_total)
    poly_loop_starts = []
    poly_loop_totals = []
    poly_loop_prev = 0
    for i, l in enumerate(me.loops):
        index = fbx_polys[i]
        if index < 0:
            poly_loop_starts.append(poly_loop_prev)
            poly_loop_totals.append((i - poly_loop_prev) + 1)
            poly_loop_prev = i + 1
            index = -(index + 1)
        l.vertex_index = index
    poly_loop_starts.append(poly_loop_prev)
    poly_loop_totals.append((i - poly_loop_prev) + 1)

    me.polygons.add(len(poly_loop_starts))
    me.polygons.foreach_set("loop_start", poly_loop_starts)
    me.polygons.foreach_set("loop_total", poly_loop_totals)

    blen_read_geom_uv(fbx_obj, me)

    me.validate(0)
    me.use_fake_user = True

    # crappy!
    obj = bpy.data.objects.new(name=elem_name_utf8, object_data=me)
    scene = bpy.data.scenes[0]
    scene.objects.link(obj)

    return me


# --------
# Material

def blen_read_material(fbx_obj):
    elem_name, elem_class = elem_split_name_class(fbx_obj)
    assert(elem_class == b'Material')
    elem_name_utf8 = elem_name.decode('utf-8')

    ma = bpy.data.materials.new(name=elem_name_utf8)

    const_color_white = 1.0, 1.0, 1.0

    fbx_props = elem_find_first(fbx_obj, b'Properties70')
    assert(fbx_props is not None)

    if use_cycles:
        pass
    else:
        # TODO, number BumpFactor isnt used yet
        ma.diffuse_color = elem_props_get_color_rgb(fbx_props, b'DiffuseColor', const_color_white)
        ma.specular_color = elem_props_get_color_rgb(fbx_props, b'SpecularColor', const_color_white)
        ma.alpha = elem_props_get_number(fbx_props, b'Opacity', 1.0)
        ma.specular_intensity = elem_props_get_number(fbx_props, b'SpecularFactor', 0.25) * 2.0
        ma.specular_hardness = elem_props_get_number(fbx_props, b'Shininess', 9.6) * 5.10 + 1.0 

    # print(fbx_props)
    ma.use_fake_user = 1
    return ma


# -------
# Texture

def blen_read_texture(fbx_obj, basedir, texture_cache):
    from bpy_extras import image_utils
    
    elem_name, elem_class = elem_split_name_class(fbx_obj)
    assert(elem_class == b'Texture')
    elem_name_utf8 = elem_name.decode('utf-8')

    # im = bpy.data.images.new(name=elem_name_utf8, width=1, height=1)
    filepath = elem_find_first_string(fbx_obj, b'FileName')
    if os.sep == '/':
        filepath = filepath.replace('\\', '/')  # unix
    else:
        filepath = filepath.replace('/', '\\')  # ms-windows

    tex = texture_cache.get(filepath)
    if tex is not None:
        # print("Using cache", tex)
        return tex

    image = image_utils.load_image(
        filepath,
        dirname=basedir,
        place_holder=True,
        )

    image.name = elem_name_utf8
    tex = bpy.data.textures.new(name=elem_name_utf8, type='IMAGE')
    tex.image = image

    texture_cache[filepath] = tex
    return tex


def main():
    elem_root = parse_bin.parse(fn)
    basedir = os.path.dirname(fn)
    texture_cache = {}

    fbx_objects = elem_find_first(elem_root, b'Objects')
    fbx_connections = elem_find_first(elem_root, b'Connections')

    if fbx_objects is None:
        return print("no 'Objects' found")
    if fbx_connections is None:
        return print("no 'Connections' found")

    for fbx_obj in fbx_objects.elems:
        assert(fbx_obj.props_type == b'LSS')
        fbx_uuid = elem_uuid(fbx_obj)
        fbx_table_object[fbx_uuid] = [fbx_obj, None]
    del fbx_obj

    # ----
    # First load in the data
    # http://download.autodesk.com/us/fbx/20112/FBX_SDK_HELP/index.html?url=WS73099cc142f487551fea285e1221e4f9ff8-7fda.htm,topicNumber=d0e6388

    fbx_connection_map = {}
    fbx_connection_map_reverse = {}

    for fbx_link in fbx_connections.elems:
        # print(fbx_link)
        c_type = fbx_link.props[0]
        c_src, c_dst = fbx_link.props[1:3]
        # if c_type == b'OO':
        
        fbx_connection_map.setdefault(c_src, []).append((c_dst, fbx_link))
        fbx_connection_map_reverse.setdefault(c_dst, []).append((c_src, fbx_link))
        a = repr((c_type,
            getattr(fbx_table_object.get(c_src, (None,))[0], "id", None), "->",
            getattr(fbx_table_object.get(c_dst, (None,))[0], "id", None)))
        
        if "Texture" in a and "Video" in a:
            pass
        elif "Texture" in a or "Video" in a:
            print(a)
        else:
            pass
            


    # ----
    # Load model data (currently mesh objects)
    # TODO

    # ----
    # Load mesh data
    for fbx_uuid, fbx_item in fbx_table_object.items():
        fbx_obj, blen_data = fbx_item
        if fbx_obj.id == b'Geometry':
            # print(fbx_obj)
            if fbx_obj.props[-1] == b'Mesh':
                assert(blen_data is None)
                fbx_item[1] = blen_read_geom(fbx_obj)

    # ----
    # Load material data
    for fbx_uuid, fbx_item in fbx_table_object.items():
        fbx_obj, blen_data = fbx_item
        if fbx_obj.id == b'Material':
            assert(blen_data is None)
            # print(fbx_obj.props)
            # if fbx_obj.props[-1] == b'Mesh':
            fbx_item[1] = blen_read_material(fbx_obj)

    # ----
    # Load image data
    for fbx_uuid, fbx_item in fbx_table_object.items():
        fbx_obj, blen_data = fbx_item
        if fbx_obj.id == b'Texture':
            fbx_item[1] = blen_read_texture(fbx_obj, basedir, texture_cache)
            # print(fbx_item[1].size[:])


    # ----
    # Load object


    # ----
    # Connections

    def connection_filter_ex(fbx_uuid, fbx_id, dct):
        return [(c_found[0], c_found[1], c_type)
                for (c_uuid, c_type) in dct.get(fbx_uuid, ())
                for c_found in (fbx_table_object[c_uuid],)
                if c_found[0].id == fbx_id]

    def connection_filter_forward(fbx_uuid, fbx_id):
        return connection_filter_ex(fbx_uuid, fbx_id, fbx_connection_map)

    def connection_filter_reverse(fbx_uuid, fbx_id):
        return connection_filter_ex(fbx_uuid, fbx_id, fbx_connection_map_reverse)

    # link Material's to Geometry (via Model's)
    for fbx_uuid, fbx_item in fbx_table_object.items():
        fbx_obj, blen_data = fbx_item
        if fbx_obj.id == b'Geometry':
            # print("Found Geometry!")
            mesh = fbx_table_object[fbx_uuid][1]
            for fbx_lnk, fbx_lnk_item, fbx_lnk_type in connection_filter_forward(fbx_uuid, b'Model'):
                fbx_lnk_uuid = elem_uuid(fbx_lnk)
                for fbx_lnk_material, material, fbx_lnk_material_type in connection_filter_reverse(fbx_lnk_uuid, b'Material'):
                    mesh.materials.append(material)

    # textures that use this material
    for fbx_uuid, fbx_item in fbx_table_object.items():
        fbx_obj, blen_data = fbx_item
        if fbx_obj.id == b'Material':
            # print("Found Material!")
            material = fbx_table_object[fbx_uuid][1]
            # print(material)
            for fbx_lnk, tex, fbx_lnk_type in connection_filter_reverse(fbx_uuid, b'Texture'):
                # print("AAA", fbx_lnk_item)
                if use_cycles:
                    pass
                else:
                    if fbx_lnk_type.props[0] == b'OP':
                        # print("OP", fbx_lnk_type)

                        mtex = material.texture_slots.add()
                        mtex.texture = tex
                        mtex.texture_coords = 'UV'
                        lnk_type = fbx_lnk_type.props[3]
                        mtex.use_map_color_diffuse = False
                        use_bumpfac = False

                        if lnk_type == b'DiffuseColor':
                            mtex.use_map_color_diffuse = True
                        elif lnk_type == b'SpecularColor':
                            mtex.use_map_color_spec = True
                        elif lnk_type == b'ReflectionColor':
                            mtex.use_map_raymir = True  # correct?
                        elif lnk_type == b'TransparentColor':
                            pass
                        elif lnk_type == b'DiffuseFactor':
                            mtex.use_map_diffuse = True
                        elif lnk_type == b'ShininessExponent':
                            mtex.use_map_hardness = True
                        elif lnk_type == b'NormalMap':
                            tex.use_normal_map = True  # not ideal!
                            mtex.use_map_normal = True
                            use_bumpfac = True
                        elif lnk_type == b'Bump':
                            mtex.use_map_normal = True
                            use_bumpfac = True
                        else:
                            print("WARNING: material link %r ignored" % lnk_type)

                        if use_bumpfac:
                            # need to get this from the material
                            fbx_props = elem_find_first(fbx_obj, b'Properties70')
                            mtex.normal_factor = elem_props_get_number(fbx_props, b'BumpFactor', 1.0)


    # sce = bpy.data.scenes[0]

    # print(output)
    # import os
    # os.system("du -h '%s'" % fn)
    bpy.ops.wm.save_as_mainfile(filepath="/tmp.blend")


# utility functions!
import sys
def run(cmd):
    print(">>> ", " ".join(cmd))
    import subprocess
    proc = subprocess.Popen(" ".join(cmd),
                            shell=True,
                            stderr=sys.stderr,
                            stdout=sys.stdout,
                            )

if __name__ == "__main__":
    try:
        import bpy
    except:
        import os
        cmd = (
            "/src/blender/blender.bin",
            "--background",
            "--env-system-scripts", "/src/blender/release/scripts",
            "--enable-autoexec",
            "--python",  __file__)

        run(cmd)
        
        import sys
        sys.exit(0)

    main()
