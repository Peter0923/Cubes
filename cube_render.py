import numpy
import moderngl as gl
from OpenGL import GL
from pyrr import Matrix44
from logger import logger
from scene_generator import unit_size
from resource_manager import ResourceManger
from scene_generator import SceneGenerator
from scene_tracker import SceneTracker

cube_max_number = 10000
cube_face_map = {0: (0, 0, unit_size), 1: (unit_size, 0, 0), 
                 2: (0, -unit_size, 0), 3: (-unit_size, 0, 0), 
                 4: (0, 0, -unit_size), 5: (0, unit_size, 0)}

class CubeRender(object):
    def __init__(self,
                 ctx: gl.Context,
                 tracker: SceneTracker):
        self.ctx = ctx
        self.tracker = tracker
        self.init_scene()
        self.init_picker()
        
    def init_scene(self):
        cube_normals = self.ctx.buffer(SceneGenerator.cube_normals()) 
        self.cube_pos = self.ctx.buffer(SceneGenerator.cube())
        self.cube_color = None
        
        # self.cubes = SceneGenerator.gen_cube_instances_0()
        self.cubes = SceneGenerator.load_cubes()
        self.tracker.reload(self.cubes)
            
        self.vbo = self.ctx.buffer(reserve = cube_max_number*24)
        self.vbo.write(numpy.array(self.cubes).astype('f4'))
        
        self.prog = ResourceManger.get_shader('scene')
        self.vao = self.ctx.vertex_array(
            self.prog, [
                (self.cube_pos, '3f /v', 'in_vert'),
                (cube_normals, '3f /v', 'in_normal'),
                (self.vbo, '3f 3f /i', 'in_offset', 'in_color')
            ])
    
    def init_picker(self):
        self.prog_pick = ResourceManger.get_shader('scene_pick')
        self.vao_pick = self.ctx.vertex_array(
            self.prog_pick, [
                (self.cube_pos, '3f /v', 'in_vert'),
                (self.vbo, '3f 12x /i', 'in_offset')
            ])
        
    def reload(self, filename = "cubes0"):
        self.cubes.clear()
        self.vbo.clear()
        if filename:
            self.cubes = SceneGenerator.load_cubes(filename)
            self.vbo.write(numpy.array(self.cubes).astype('f4'))
        self.tracker.reload(self.cubes)
    
    def save(self, filename = "cubes0"):
        SceneGenerator.save_cubes(self.cubes, filename)
     
    def set_projection(self, proj: Matrix44):
        self.prog['proj'].write(proj.astype('f4'))
        self.prog_pick['proj'].write(proj.astype('f4'))
        
    def update_view(self, mv: Matrix44):
        self.prog['mv'].write(mv.astype('f4'))
        self.prog_pick['mv'].write(mv.astype('f4'))
    
    def add_cube(self, x, y, eye = None):
        if self.cube_number == cube_max_number:
            logger.warning(f"Reached the maximum number {cube_max_number}!")
            return
        
        GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
        pixel = GL.glReadPixels(x, y, 1, 1, GL.GL_RGBA, GL.GL_FLOAT)
        data = pixel[0][0]
        face_id = int(data[3])
        if face_id >= 0:
            pos = (data[0] + cube_face_map[face_id][0], 
                   data[1] + cube_face_map[face_id][1], 
                   data[2] + cube_face_map[face_id][2])
            
            if pos[2] < 0:
                logger.warning("Cannot adding cube below ground!")
                return
            
            if eye is not None:
                if SceneTracker.is_clashed(pos, eye):
                    logger.warning("Too close to eye!")
                    return
            
            color = self.cube_color
            if color is None:
                color = (numpy.random.uniform(0,1),
                         numpy.random.uniform(0,1),
                         numpy.random.uniform(0,1))
                  
            new_cube = [pos[0], pos[1], pos[2], color[0], color[1], color[2]]
            self.cubes.extend(new_cube)
            self.vbo.write(numpy.array(new_cube).astype('f4'), 24*(self.cube_number-1))
            self.tracker.add_cube(pos)
    
    def remove_cube(self, x, y):
        if self.cube_number <= 0:
            logger.warning("No cubes in the scene!")
            return
        
        GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT1)
        data = GL.glReadPixels(x, y, 1, 1, GL.GL_RED, GL.GL_FLOAT)
        id = int(data[0][0])
        if id >= 0:
            del_cube = self.cubes[6*id : 6*id+3]
            del self.cubes[6*id : 6*(id+1)]
            self.vbo.write(numpy.array(self.cubes).astype('f4'))
            self.tracker.remove_cube(del_cube)
    
    @property
    def cube_number(self):
        return int(len(self.cubes) / 6)
    
    def render_picker(self):
        self.vao_pick.render(gl.TRIANGLES, instances=self.cube_number)
        
    def render(self):
        self.vao.render(gl.TRIANGLES, instances=self.cube_number)