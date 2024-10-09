import numpy
import moderngl as gl
from pyrr import Matrix44
from resource_manager import ResourceManger
from scene_generator import SceneGenerator
from scene_generator import ground_width

class GroundRender():
    def __init__(self, 
                 ctx: gl.Context):
        self.ctx = ctx
        self.init_scene()
        self.init_picker()
        
    def init_scene(self):
        self.prog = ResourceManger.get_shader('ground')
        grid_data = SceneGenerator.grid()
        vbo = self.ctx.buffer(grid_data.astype('f4'))
        self.vao = self.ctx.vertex_array(self.prog, vbo, 'in_vert')
    
    def init_picker(self):
        self.prog_pick = ResourceManger.get_shader('ground_pick')
        vbo = self.ctx.buffer(numpy.array([
            -ground_width, ground_width, 0, 0, 1,
            -ground_width, -ground_width, 0,  0, 0, 
            ground_width, ground_width, 0, 1, 1,
            ground_width, -ground_width, 0, 1, 0
            ]).astype('f4'))
        self.vao_pick = self.ctx.vertex_array(self.prog_pick, vbo, 'in_vert', 'in_texCoord')
        
        # generate texture for pick up
        width = int(ground_width*2)
        pixel = SceneGenerator.gridOffsetTexture(width)
        self.texture = self.ctx.texture((width, width), 4, pixel, dtype='f4')
        self.texture.filter = gl.NEAREST, gl.NEAREST
        self.texture.use(0)
    
    def set_projection(self, proj: Matrix44):
        self.prog['proj'].write(proj.astype('f4'))
        self.prog_pick['proj'].write(proj.astype('f4'))
        
    def update_view(self, mv: Matrix44):
        self.prog['mv'].write(mv.astype('f4'))
        self.prog_pick['mv'].write(mv.astype('f4'))
    
    def render_picker(self):
        self.vao_pick.render(gl.TRIANGLE_STRIP)
        
    def render(self):
        self.vao.render(gl.LINES)

