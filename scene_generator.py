import numpy
from enum import Enum
from os import path

# grid size: (2*ground_width) * (2*ground_width)
# unit size: (2*ground_width) / (ground_steps-1)
unit_size = 1
half_unit = 0.5
ground_width = 15.5

ground_steps = int(ground_width*2 / unit_size) + 1
base_center = (0, 0, half_unit)

# actor size:
body_height = 1.5 * unit_size  #not higher than 2 units
body_clash = 0.1 * unit_size

# color plate
colors = {
    0: None,
    1: (1.0, 0.0, 0.0),
    2: (1.0, 0.5, 0.0),
    3: (1.0, 1.0, 0.0),
    4: (0.0, 1.0, 0.0),
    5: (0.0, 1.0, 1.0),
    6: (0.0, 0.0, 1.0),
    7: (0.5, 0.0, 1.0),
    8: (0.5, 0.5, 0.0),
    9: (0.1, 0.1, 0.1)
    }

# key actions
class KeyActions(Enum):
    FORWARD = 0
    BACKWARD = 1
    LEFT = 2
    RIGHT = 3
    JUMP = 4
    UP = 5
    DOWN = 6

class SceneGenerator(object):
    @classmethod
    def grid(cls, 
             size = ground_width, 
             steps = ground_steps):
        u = numpy.repeat(numpy.linspace(-size, size, steps), 2)
        v = numpy.tile([-size, size], steps)
        w = numpy.zeros(steps * 2)
        return numpy.concatenate([numpy.dstack([u, v, w]), numpy.dstack([v, u, w])])
    
    @classmethod
    def is_in_grid(cls, point):
        if (-ground_width<=point[0]<=ground_width) and (-ground_width<=point[1]<=ground_width):
            return True
        return False  
    
    @classmethod
    def gridOffsetTexture(cls, 
                          size = int(ground_width*2), 
                          unit = unit_size):
        center_offset = (size/unit - 1) / 2
        texImage = numpy.zeros((size, size, 4), dtype=numpy.float32)
        for i in range(size):
            c = i // unit
            for j in range(size):
                r = j // unit 
                texImage[i][j][0] = (r - center_offset) * unit
                texImage[i][j][1] = (c - center_offset) * unit
                texImage[i][j][2] = -unit
                texImage[i][j][3] = 0.0
        return texImage.astype('f4')
    
    @classmethod
    def cube(cls, 
             size = unit_size, 
             center = base_center):
        l, w, h = size/2.0, size/2.0, size/2.0
        pos = numpy.array([
            center[0] + l, center[1] - w, center[2] + h,
            center[0] + l, center[1] + w, center[2] + h,
            center[0] - l, center[1] - w, center[2] + h,
            center[0] + l, center[1] + w, center[2] + h,
            center[0] - l, center[1] + w, center[2] + h,
            center[0] - l, center[1] - w, center[2] + h,
            center[0] + l, center[1] - w, center[2] - h,
            center[0] + l, center[1] + w, center[2] - h,
            center[0] + l, center[1] - w, center[2] + h,
            center[0] + l, center[1] + w, center[2] - h,
            center[0] + l, center[1] + w, center[2] + h,
            center[0] + l, center[1] - w, center[2] + h,
            center[0] + l, center[1] - w, center[2] - h,
            center[0] + l, center[1] - w, center[2] + h,
            center[0] - l, center[1] - w, center[2] + h,
            center[0] + l, center[1] - w, center[2] - h,
            center[0] - l, center[1] - w, center[2] + h,
            center[0] - l, center[1] - w, center[2] - h,
            center[0] - l, center[1] - w, center[2] + h,
            center[0] - l, center[1] + w, center[2] + h,
            center[0] - l, center[1] + w, center[2] - h,
            center[0] - l, center[1] - w, center[2] + h,
            center[0] - l, center[1] + w, center[2] - h,
            center[0] - l, center[1] - w, center[2] - h,
            center[0] + l, center[1] + w, center[2] - h,
            center[0] + l, center[1] - w, center[2] - h,
            center[0] - l, center[1] - w, center[2] - h,
            center[0] + l, center[1] + w, center[2] - h,
            center[0] - l, center[1] - w, center[2] - h,
            center[0] - l, center[1] + w, center[2] - h,
            center[0] + l, center[1] + w, center[2] - h,
            center[0] - l, center[1] + w, center[2] - h,
            center[0] + l, center[1] + w, center[2] + h,
            center[0] - l, center[1] + w, center[2] - h,
            center[0] - l, center[1] + w, center[2] + h,
            center[0] + l, center[1] + w, center[2] + h,
        ])
        return pos.astype('f4')
    
    @classmethod
    def cube_normals(cls):
        normal_data = numpy.array([
                -0, 0, 1,
                -0, 0, 1,
                -0, 0, 1,
                0, 0, 1,
                0, 0, 1,
                0, 0, 1,
                1, 0, 0,
                1, 0, 0,
                1, 0, 0,
                1, 0, 0,
                1, 0, 0,
                1, 0, 0,
                0, -1, 0,
                0, -1, 0,
                0, -1, 0,
                0, -1, 0,
                0, -1, 0,
                0, -1, 0,
                -1, -0, 0,
                -1, -0, 0,
                -1, -0, 0,
                -1, -0, 0,
                -1, -0, 0,
                -1, -0, 0,
                0, 0, -1,
                0, 0, -1,
                0, 0, -1,
                0, 0, -1,
                0, 0, -1,
                0, 0, -1,
                0, 1, 0,
                0, 1, 0,
                0, 1, 0,
                0, 1, 0,
                0, 1, 0,
                0, 1, 0,
            ])
        return normal_data.astype('f4')
    
    @classmethod
    def gen_cube_instances_0(cls):
        half_unit = unit_size / 2
        cube_instances = [
            -ground_width+half_unit, -ground_width+half_unit, 0.0, 
            0.8, 0.0, 0.0,
            ground_width-half_unit, -ground_width+half_unit, 0.0, 
            0.0, 0.8, 0.0,
            ground_width-half_unit, ground_width-half_unit, 0.0,
            0.0, 0.0, 0.8,
            -ground_width+half_unit, ground_width-half_unit, 0.0,
            0.8, 0.8, 0.0
        ]
        return cube_instances
    
    @classmethod
    def gen_cube_instances_1(cls):
        cube_instances = []
        for x in range(-5*unit_size, 5*unit_size, unit_size):
            for y in range(-5*unit_size, 5*unit_size, unit_size):
                for z in range(-4*unit_size, 4*unit_size, unit_size):
                    cube_instances.extend([x, y, z])
                    cube_instances.extend([
                        numpy.random.uniform(0, 1),
                        numpy.random.uniform(0, 1),
                        numpy.random.uniform(0, 1)])
        return cube_instances