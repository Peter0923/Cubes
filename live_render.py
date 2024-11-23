import numpy
import moderngl as gl
from pyrr import Matrix44
from resource_manager import ResourceManger
from scene_objects import SceneObjects
from scene_generator import SceneGenerator, unit_size
from scene_tracker import SceneTracker

max_number = 200

class LiveCubeRender(object):
    def __init__(self,
                 ctx: gl.Context,
                 tracker: SceneTracker):
        self.tracker = tracker
        self.prog = ResourceManger.get_shader('live_cube')
        cube_pos = ctx.buffer(SceneGenerator.cube())
        cube_normals = ctx.buffer(SceneGenerator.cube_normals())
        
        self.cubes.extend(SceneObjects.load_cubes("live"))
        self.vbo = ctx.buffer(reserve = max_number*36)
        self.vbo.write(numpy.array(self.cubes).astype('f4'))
        self.tracker.reload_live_cubes(self.cubes)
        
        self.vao = ctx.vertex_array(
            self.prog, [
                (cube_pos, '3f /v', 'in_vert'),
                (cube_normals, '3f /v', 'in_normal'),
                (self.vbo, '3f 3f 3f /i', 'in_offset', 'in_dir', 'in_color')
            ])
       
    def init_cubes(self):
        color =  (0.5, 0.5, 0.0)   
        center = (0.0, 0.0, 4*unit_size)
        dir = (0, 3, 0)
        self.add_cube(center, dir, color)
        center = (10.0, 0.0, 4*unit_size)
        dir = (3, 0, 0)
        self.add_cube(center, dir, color)
        center = (0.0, 10.0, 2*unit_size)
        dir = (0, 0, 3)
        self.add_cube(center, dir, color)
    
    def save(self, file_name = "live"):
        SceneObjects.save_live_cubes(self.cubes, file_name)
              
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
    def cubes(self):
        return SceneObjects.live_cubes
        
    @property
    def cube_number(self):
        return int(len(self.cubes) / 9)