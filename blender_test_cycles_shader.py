import bpy


COL = 200
ROW = 200

class CyclesShaderWrapper():
    __slots__ = (        
        "material",

        "node_out",
        "node_mix_shader_spec",
        "node_mix_shader_alpha",  # diffuse/alpha mix

        "node_bsdf_alpha",
        "node_bsdf_diff",
        "node_bsdf_spec",

        "node_mix_color_alpha",
        "node_mix_color_diff",
        "node_mix_color_spec",
        "node_mix_color_spec_hard",
        
        "node_normal_map",
        )

    def __init__(self, material):
        """
        Hard coded shader setup.
        Suitable for importers, adds basic diffuse/spec/alpha/normal.
        """
        
        COLOR_WHITE = 1.0, 1.0, 1.0, 1.0
        COLOR_BLACK = 0.0, 0.0, 0.0, 1.0
        
        self.material = material
        self.material.use_nodes = True

        tree = self.material.node_tree

        nodes = tree.nodes
        links = tree.links
        
        nodes.clear()

        # ----
        # Add shaders
        node = nodes.new(type='ShaderNodeOutputMaterial')
        node.label = "Material Out"
        node.location = 5 * COL, 4 * ROW
        self.node_out = node
        del node

        node = nodes.new(type='ShaderNodeAddShader')
        node.label = "Shader Add Spec"
        node.location = 4 * COL, 4 * ROW
        self.node_mix_shader_spec = node
        # Link
        links.new(self.node_mix_shader_spec.outputs["Shader"],
                  self.node_out.inputs["Surface"])
        del node

        # --------------------------------------------------------------------
        # Alpha

        # ----
        # Mix shader
        node = nodes.new(type='ShaderNodeMixShader')
        node.label = "Shader Mix Alpha"
        node.location = 3 * COL, 4 * ROW
        node.inputs["Fac"].default_value = 1.0  # no alpha by default
        self.node_mix_shader_alpha = node
        # Link
        links.new(self.node_mix_shader_alpha.outputs["Shader"],
                  self.node_mix_shader_spec.inputs[0])
        del node
        # Alpha BSDF
        node = nodes.new(type='ShaderNodeBsdfTransparent')
        node.label = "Alpha BSDF"
        node.location = 2 * COL, 4 * ROW
        self.node_bsdf_alpha = node
        # Link
        links.new(self.node_bsdf_alpha.outputs["BSDF"],
                  self.node_mix_shader_alpha.inputs[1])  # first 'Shader'
        del node
        # Mix Alpha Color
        node = nodes.new(type='ShaderNodeMixRGB')
        node.label = "Mix Color/Alpha"
        node.location = 1 * COL, 5 * ROW
        node.blend_type = 'MULTIPLY'
        node.inputs["Fac"].default_value = 1.0
        node.inputs["Color1"].default_value = COLOR_WHITE
        node.inputs["Color2"].default_value = COLOR_WHITE
        self.node_mix_color_alpha = node
        links.new(self.node_mix_color_alpha.outputs["Color"],
                  self.node_mix_shader_alpha.inputs["Fac"])
        del node

        # --------------------------------------------------------------------
        # Diffuse

        # Diffuse BSDF
        node = nodes.new(type='ShaderNodeBsdfDiffuse')
        node.label = "Diff BSDF"
        node.location = 2 * COL, 3 * ROW
        self.node_bsdf_diff = node
        # Link
        links.new(self.node_bsdf_diff.outputs["BSDF"],
                  self.node_mix_shader_alpha.inputs[2])  # first 'Shader'
        del node

        # Mix Diffuse Color
        node = nodes.new(type='ShaderNodeMixRGB')
        node.label = "Mix Color/Diffuse"
        node.location = 1 * COL, 3 * ROW
        node.blend_type = 'MULTIPLY'
        node.inputs["Fac"].default_value = 1.0
        node.inputs["Color1"].default_value = COLOR_WHITE
        node.inputs["Color2"].default_value = COLOR_WHITE
        self.node_mix_color_diff = node
        links.new(self.node_mix_color_diff.outputs["Color"],
                  self.node_bsdf_diff.inputs["Color"])
        del node

        # --------------------------------------------------------------------
        # Specular
        node = nodes.new(type='ShaderNodeBsdfGlossy')
        node.label = "Spec BSDF"
        node.location = 2 * COL, 1 * ROW
        self.node_bsdf_spec = node
        # Link (with add shader)
        links.new(self.node_bsdf_spec.outputs["BSDF"],
                  self.node_mix_shader_spec.inputs[1])  # second 'Shader' slot
        del node

        node = nodes.new(type='ShaderNodeMixRGB')
        node.label = "Mix Color/Diffuse"
        node.location = 1 * COL, 1 * ROW
        node.blend_type = 'MULTIPLY'
        node.inputs["Fac"].default_value = 1.0
        node.inputs["Color1"].default_value = COLOR_WHITE
        node.inputs["Color2"].default_value = COLOR_BLACK
        self.node_mix_color_spec = node
        # Link
        links.new(self.node_mix_color_spec.outputs["Color"],
                  self.node_bsdf_spec.inputs["Color"])
        del node

        node = nodes.new(type='ShaderNodeMixRGB')
        node.label = "Mix Color/Hardness"
        node.location = 0 * COL, 1 * ROW
        node.blend_type = 'MULTIPLY'
        node.inputs["Fac"].default_value = 1.0
        node.inputs["Color1"].default_value = COLOR_WHITE
        node.inputs["Color2"].default_value = COLOR_BLACK
        self.node_mix_color_spec_hard = node
        # Link
        links.new(self.node_mix_color_spec_hard.outputs["Color"],
                  self.node_bsdf_spec.inputs["Roughness"])
        del node

        # --------------------------------------------------------------------
        # Normal Map
        node = nodes.new(type='ShaderNodeNormalMap')
        node.label = "Normal/Map"
        node.location = 1 * COL, 2 * ROW
        node.mute = True  # unmute on use
        self.node_normal_map = node
        # Link (with diff shader)
        links.new(self.node_normal_map.outputs["Normal"],
                  self.node_bsdf_diff.inputs["Normal"])
        # Link (with spec shader)
        links.new(self.node_normal_map.outputs["Normal"],
                  self.node_bsdf_spec.inputs["Normal"])
        del node

    @staticmethod
    def _image_create_helper(image, node_dst, sockets_dst):
        tree = node_dst.id_data
        nodes = tree.nodes
        links = tree.links

        node = nodes.new(type='ShaderNodeTexImage')
        node.image = image
        node.location = node_dst.location
        node.location.x -= COL
        for socket in sockets_dst:
            links.new(node.outputs["Color"],
                      socket)
        return node

    def diffuse_color_set(self, color):
        self.node_mix_color_diff.inputs["Color1"].default_value[0:3] = color

    def diffuse_image_set(self, image):
        self._image_create_helper(image,
            self.node_mix_color_diff,
            (self.node_mix_color_diff.inputs["Color2"],))

    def specular_color_set(self, color):
        self.node_mix_color_spec.inputs["Color1"].default_value[0:3] = color

    def specular_image_set(self, image):
        self._image_create_helper(image,
            self.node_mix_color_spec,
            (self.node_mix_color_spec.inputs["Color2"],))

    def hardness_value_set(self, value):
        self.node_mix_color_spec_hard.inputs["Color1"].default_value = (value,) * 4

    def hardness_image_set(self, image):
        self._image_create_helper(image,
            self.node_mix_color_spec_hard,
            (self.node_mix_color_spec_hard.inputs["Color2"],))

    def alpha_value_set(self, value):
        self.node_mix_color_alpha.inputs["Color1"].default_value = (value,) * 4

    def alpha_image_set(self, image):
        self._image_create_helper(image,
            self.node_mix_color_alpha,
            (self.node_mix_color_alpha.inputs["Color2"],))

    def normal_factor_set(self, value):
        self.node_normal_map.inputs["Strength"].default_value = value

    def normal_image_set(self, image):
        self.node_normal_map.mute = False

        self._image_create_helper(image,
            self.node_normal_map,
            (self.node_normal_map.inputs["Color"],))


if 0:
    image = bpy.data.images.load(filepath="/canvas.png")

    material = bpy.data.materials.new(name="Test")
    mwrap = CyclesShaderWrapper(material)
    mwrap.diffuse_color_set((0.5, 0.5, 0.5))
    mwrap.hardness_set(1.0)
    # mwrap.specular_image_set(image)
    #mwrap.normal_image_set(image)
    # mwrap.normal_factor_set(0.1)
    # mwrap.specular_color_set((0, 0, 1, 1))
    # mwrap.alpha_value_set(0.5)

    bpy.context.object.data.materials[0] = mwrap.material
