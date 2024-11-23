from math import sin
from pyrr import Vector3
from scene_generator import base_center, unit_size
from scene_objects import Grid3D, SceneObjects

class LiveCube(object):
    def __init__(self, index):
        center = SceneObjects.live_cubes[9*index : 9*index+3]
        dir = SceneObjects.live_cubes[9*index+3 : 9*index+6]
        self.cube = Vector3(center) + Vector3(base_center)
        self.dir = Vector3(dir)
        self.dir_norm = self.dir.normalized
        
    def get_position(self, time: float):
        return self.cube + (1.0 - sin(time)) * self.dir
    
    def get_range(self):
        end = self.cube + 2 * self.dir
        end = Grid3D.point_3d_to_index(end)
        start = Grid3D.point_3d_to_index(self.cube)
        while (start != end):
            yield start
            start = (start[0] + self.dir_norm[0], 
                     start[1] + self.dir_norm[1],
                     start[2] + self.dir_norm[2])
        yield end
 
# Link eye with cube
# live cube position = pos + 3.0*(1.0 - sin(time))
class Linkage(object):
    def __init__(self):
        self.linked = False
    
    def start_link(self, 
                   live_cube: LiveCube,
                   eye_pos: Vector3,
                   time: float):
        self.linked = True
        self.cube = live_cube
        self.offset = eye_pos - self.cube.get_position(time)
         
    def update_offset(self, offset):
        self.offset.x += offset.x
        self.offset.y += offset.y
    
    def get_linked_eye(self, time):
        cube_pos = self.cube.get_position(time)
        return cube_pos + self.offset
        
    def end_link(self):
        self.linked = False