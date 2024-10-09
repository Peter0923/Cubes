import numpy
import moderngl as gl
from pyrr import Matrix44
from resource_manager import ResourceManger

class CrossRender():
    def __init__(self, 
                 ctx: gl.Context,
                 ratio):
        
        half_width = 0.012
        half_height = half_width * ratio
        
        prog = ResourceManger.get_shader('cross')
        vertices = numpy.array([
            -half_width, 0.0, 0.0,
            half_width, 0.0, 0.0,
            0.0, -half_height, 0.0,
            0.0, half_height, 0.0])
        
        vbo = ctx.buffer(vertices.astype('f4'))
        self.vao = ctx.vertex_array(prog, vbo, 'in_vert') 
        
    def render(self):
        self.vao.render(gl.LINES)

