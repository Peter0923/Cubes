import numpy
import moderngl as gl
from pyrr import Matrix44
from resource_manager import ResourceManger
from scene_objects import SceneObjects
from scene_generator import SceneGenerator, unit_size
from scene_tracker import SceneTracker

max_number = 200
face_map = {0: (0, 0, unit_size), 1: (unit_size, 0, 0), 
            2: (0, -unit_size, 0), 3: (-unit_size, 0, 0), 
            4: (0, 0, -unit_size), 5: (0, unit_size, 0)}

class LiveCubeRender(object):
    def __init__(self,
                 ctx: gl.Context,
                 tracker: SceneTracker):
        self.tracker = tracker
        self.prog = ResourceManger.get_shader('live_cube')
        cube_pos = ctx.buffer(SceneGenerator.cube())
        cube_normals = ctx.buffer(SceneGenerator.cube_normals())
        self.vbo = ctx.buffer(reserve = max_number*36)
        
        self.vao = ctx.vertex_array(
            self.prog, [
                (cube_pos, '3f /v', 'in_vert'),
                (cube_normals, '3f /v', 'in_normal'),
                (self.vbo, '3f 3f 3f /i', 'in_offset', 'in_dir', 'in_color')
            ])
        self.init_cubes()
       
    def init_cubes(self):
        self.cubes = SceneObjects.live_cubes
        color =  (0.5, 0.5, 0.0)
        
        center = (0.0, 0.0, 4*unit_size)
        dir = (0, 1, 0)
        self.add_cube(center, dir, color)
        
        center = (10.0, 0.0, 4*unit_size)
        dir = (1, 0, 0)
        self.add_cube(center, dir, color)
        
        center = (0.0, 10.0, 2*unit_size)
        dir = (0, 0, 1)
        self.add_cube(center, dir, color)
              
    def set_projection(self, proj: Matrix44):
        self.prog['proj'].write(proj.astype('f4'))
        
    def update_view(self, mv: Matrix44):
        self.prog['mv'].write(mv.astype('f4'))
    
    def update_time(self, time: float):
        self.prog['time'].value = time
    
    def add_cube(self, pos, dir, color):          
        new_cube = [pos[0], pos[1], pos[2], 
                    dir[0], dir[1], dir[2],
                    color[0], color[1], color[2]]
        self.cubes.extend(new_cube)
        self.vbo.write(numpy.array(new_cube).astype('f4'), 36*(self.cube_number-1))
        self.tracker.add_live_cube(self.cube_number - 1)
        
    def render(self):
        self.vao.render(gl.TRIANGLES, instances=self.cube_number)
        
    @property
    def cube_number(self):
        return int(len(self.cubes) / 9)