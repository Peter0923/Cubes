from os import path
from pyrr import Vector3
from logger import logger
from scene_generator import half_unit, unit_size, body_height, body_clash, base_center
from resource_manager import ResourceManger

cube_faces = ((1, 0, 0), (-1, 0, 0), 
              (0, 1, 0), (0, -1, 0), 
              (0, 0, 1), (0, 0, -1))

class Box3D(object):
    def __init__(self, min: Vector3, max: Vector3):
        self.min = min
        self.max = max

class AABB(object):
    # check intersection and penetration
    @classmethod
    def get_penetration(cls, eye: Vector3, center: Vector3):
        eye_box = cls._from_eye(eye)
        cube_box = cls._from_cube(center)
        if cls._is_intersect(eye_box, cube_box):
            return cls._get_penetration(eye_box, cube_box)
        return None
        
    # clash detection between actor and cube
    @classmethod
    def is_intersect(cls, eye: Vector3, center: Vector3):
        eye_box = cls._from_eye(eye)
        cube_box = cls._from_cube(center)
        return cls._is_intersect(eye_box, cube_box)
    
    # is actor land on cube when intersected
    @classmethod
    def is_land_on(cls, eye: Vector3, center: Vector3):
        eye_box = cls._from_eye(eye)
        eye_box.min.z -= half_unit
        cube_box = cls._from_cube(center)
        return cls._is_intersect(eye_box, cube_box)
       
    @classmethod
    def _from_eye(cls, pos: Vector3):
        min = Vector3([pos.x-body_clash, pos.y-body_clash, pos.z-body_height])
        max = Vector3([pos.x+body_clash, pos.y+body_clash, pos.z+body_clash])
        return Box3D(min, max)
    
    @classmethod
    def _from_cube(cls, center: Vector3):
        half_size = Vector3([half_unit, half_unit, half_unit])
        return Box3D(center-half_size, center+half_size)
    
    @classmethod
    def _is_intersect(cls, box1:Box3D, box2:Box3D):
         return (
            box1.min.x < box2.max.x and
            box1.min.y < box2.max.y and
            box1.min.z < box2.max.z and
            box1.max.x > box2.min.x and 
            box1.max.y > box2.min.y and
            box1.max.z > box2.min.z)
    
    @classmethod
    def _get_penetration(cls, box1:Box3D, box2:Box3D):
        distances = ((box1.max.x - box2.min.x),
                     (box2.max.x - box1.min.x),
                     (box1.max.y - box2.min.y),
                     (box2.max.y - box1.min.y),
                     (box1.max.z - box2.min.z),
                     (box2.max.z - box1.min.z))
        
        p_face = None
        p_value = unit_size
        for i in range(6):
            if distances[i] < p_value:
                p_value = distances[i]
                p_face = cube_faces[i]
        penetration = p_value * Vector3(p_face)
        return penetration

class Grid3D(object):
    @classmethod
    def get_box_2d(cls, eye: Vector3):
        left = eye.x - body_clash
        right = eye.x + body_clash
        bottom = eye.y - body_clash
        top = eye.y + body_clash
        corners = ((left, top), (right, top), (right, bottom), (left, bottom))
        return corners
    
    @classmethod
    def get_grids(cls, eye: Vector3, dir = 0):
        z_grid = cls.get_all_z_index(eye.z)
        if dir is None:   #move
            z_grid = z_grid[:2]
        elif dir == 1:   #fly up
            z_grid = z_grid[:1]
        elif dir == -1:   #fly down
            z_grid = z_grid[2:]
        elif z_grid[1] == z_grid[2]:   #free
            z_grid = z_grid[:2]
        
        xy_grid = cls.get_all_xy_index(eye)
        for z in reversed(z_grid):
            for x,y in xy_grid:
                yield(x, y, z)
    
    @classmethod
    def get_all_xy_index(cls, pos: Vector3):
        left = pos.x - body_clash - base_center[0] 
        right = pos.x + body_clash - base_center[0]
        bottom = pos.y - body_clash - base_center[1]
        top = pos.y + body_clash - base_center[1]
        corners = cls.offsets_to_index((left, right, bottom, top))
        return ((corners[0], corners[3]),
                (corners[1], corners[3]),
                (corners[1], corners[2]),
                (corners[0], corners[2]))
    
    @classmethod
    def get_all_z_index(cls, eye_z_pos):
        eye_dz = eye_z_pos + body_clash - base_center[2]
        leg_dz = eye_z_pos - unit_size - base_center[2]
        foot_dz = eye_z_pos - body_height - base_center[2]
        return cls.offsets_to_index((eye_dz, leg_dz, foot_dz))
        
    @classmethod
    def point_2d_to_index(cls, point):
        dx = point[0] - base_center[0]
        dy = point[1] - base_center[1]
        index_x = int((dx+half_unit)/unit_size) if dx>=0 else int((dx-half_unit)/unit_size)
        index_y = int((dy+half_unit)/unit_size) if dy>=0 else int((dy-half_unit)/unit_size)
        return (index_x, index_y)
    
    @classmethod
    def point_3d_to_index(cls, point):
        dx = point[0] - base_center[0]
        dy = point[1] - base_center[1]
        dz = point[2] - base_center[2]
        return cls.offset_3d_to_index((dx, dy, dz))
          
    @classmethod
    def offset_3d_to_index(cls, offset):
        index_x = int((offset[0]+half_unit)/unit_size) if offset[0]>=0 else int((offset[0]-half_unit)/unit_size)
        index_y = int((offset[1]+half_unit)/unit_size) if offset[1]>=0 else int((offset[1]-half_unit)/unit_size)
        index_z = int((offset[2]+half_unit)/unit_size) if offset[2]>=0 else int((offset[2]-half_unit)/unit_size)
        return (index_x, index_y, index_z)
    
    @classmethod
    def offsets_to_index(cls, offsets):
        all_index = []
        for offset in offsets:
            index = int((offset+half_unit)/unit_size) if offset>=0 else int((offset-half_unit)/unit_size)
            all_index.append(index)
        return all_index

class SceneObjects(object):
    cubes = []
    live_cubes = []
    
    @classmethod
    def load_cubes(cls, name: str):
        try:
            data = ResourceManger.load_data(f"data/{name}.scene")
        except:
            logger.error(f"Error reading file: {name}.scene")
            return []
        else:
            cubes = list(map(float, data.split()))
            return cubes
    
    @classmethod
    def save_cubes(cls, cubes: list, name: str):
        length = len(cubes)
        file_path = path.join(ResourceManger.resource_dir, f"data/{name}.scene")
        with open(file_path, "w") as file:
            for i in range(0, length, 6):
                file.write("{:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}\n".format(
                    cubes[i], cubes[i+1], cubes[i+2], cubes[i+3], cubes[i+4], cubes[i+5]))
    
    @classmethod
    def save_live_cubes(cls, live_cubes: list, name: str):
        length = len(live_cubes)
        file_path = path.join(ResourceManger.resource_dir, f"data/{name}.scene")
        with open(file_path, "w") as file:
            for i in range(0, length, 9):
                file.write("{:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}\n".format(
                    live_cubes[i], live_cubes[i+1], live_cubes[i+2], 
                    live_cubes[i+3], live_cubes[i+4], live_cubes[i+5],
                    live_cubes[i+6], live_cubes[i+7], live_cubes[i+8]))