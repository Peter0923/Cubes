from enum import Enum
from pyrr import Vector3
from logger import logger 
from scene_generator import *
from resource_manager import ResourceManger
from scene_objects import AABB, Grid3D
from scene_linker import LiveCube

ZERO = 1e-6

class ClashType(Enum):
    NoClash = 0
    Static = 1
    LiveNZ = 2
    LivePZ = 3
    LiveXY = 4
    
class ClashDetector(object):
    def __init__(self, scene_map, live_map):
        self.scene_map = scene_map
        self.live_map = live_map
        self.live_cube = None  #potential clashed live cube
        self.clash_points = 0x00
        self.move_direction = 0x00
        self.land_sound = ResourceManger.get_audio('solid')
        
    def detect_clash_in_move(self,
                             from_pos: Vector3,
                             to_pos: Vector3):
        self.clash_points = self._get_clash_points(to_pos)
        return self._decide_next_move(from_pos, to_pos)
    
    def detect_clash_in_fly(self, 
                            to_pos: Vector3,
                            dir):   #1(Up), 0(Free), -1(Down) 
        # landing
        foot = to_pos.z - body_height
        if foot<0 and SceneGenerator.is_in_grid(to_pos.xy):
            self.land_sound.play()
            return True
        
        for grid in Grid3D.get_grids(to_pos, dir):
            if grid in self.scene_map:
                return True
        return False
    
    def is_on_air(self, eye_pos: Vector3):
        foot = eye_pos.z - body_height
        if (foot<base_center[2]) and (SceneGenerator.is_in_grid(eye_pos.xy)):
            return False
        
        foot -= half_unit
        z_index = int(foot / unit_size)
        corners = Grid3D.get_box_2d(eye_pos)
        for corner in corners:
            x, y = Grid3D.point_2d_to_index(corner)
            if (x, y, z_index) in self.scene_map:
                return False
        return True
    
    def is_land_on_cube(self, eye_pos: Vector3, center: Vector3):
        center_index = Grid3D.offset_3d_to_index(center)
        z_index = int((eye_pos.z-body_height-half_unit) / unit_size)
        corners = Grid3D.get_box_2d(eye_pos)
        for corner in corners:
            x, y = Grid3D.point_2d_to_index(corner)
            if (x, y, z_index) == center_index:
                return True
        return False
    
    def detect_clash_with_live_cube(self, eye: Vector3, time: float):
        for grid in Grid3D.get_grids(eye):
            if grid in self.live_map:
                index = self.live_map[grid]
                self.live_cube = LiveCube(index)
                pos = self.live_cube.get_position(time) 
                return AABB.get_penetration(eye, pos)
        return None
        
    def is_clash_with_live_cube(self, eye: Vector3, time: float):
        for grid in Grid3D.get_grids(eye, None):
            if grid in self.live_map:
                index = self.live_map[grid]
                self.live_cube = LiveCube(index)
                pos = self.live_cube.get_position(time) 
                return AABB.is_intersect(eye, pos)
        return False
        
    def is_land_on_live_cube(self, eye: Vector3, time: float):
        pos = self.live_cube.get_position(time)
        return AABB.is_land_on(eye, pos)
    
    def reset_eye_position(self, eye_pos: Vector3):
        eye_z = eye_pos.z
        x, y, z = Grid3D.point_3d_to_index(eye_pos.tolist())
        while ((x, y, z) in self.scene_map) or ((x, y, z-1) in self.scene_map): 
            z += 1
            eye_z += unit_size
        while z>1 and ((x, y, z-2) not in self.scene_map):
            z -= 1
            eye_z -= unit_size
        if z<=1 and (not SceneGenerator.is_in_grid(eye_pos.xy)):
            return None  
        return Vector3([eye_pos.x, eye_pos.y, eye_z])
    
    # Validate if we can place cube in the position
    # 0: Ok to put
    # 1: Below ground is not allowed
    # 2: Clash with static cube
    # 3: Clash with Live cube
    # 4: Clash with eye 
    def validate_placement(self, target, eye_pos: Vector3=None):
        if target[2] < 0:
            logger.warning("Cannot put cube below ground!")
            return False
        
        cube = Grid3D.offset_3d_to_index(target)
        if cube in self.scene_map:
            logger.warning("Clash with static cube!")
            return False
        if cube in self.live_map:
            logger.warning("Clash with live cube!")
            return False
        
        if eye_pos is not None:
            for grid in Grid3D.get_grids(eye_pos):
                if cube == grid:
                    logger.warning("Too close to eye!")
                    return False
        return True
          
    def _get_clash_points(self, pos: Vector3):
        index = 0x01
        clash_points = 0x00
        corners = Grid3D.get_box_2d(pos)
        eye_z = int(pos.z / unit_size)
        for corner in corners:
            clash = 0x00
            x, y = Grid3D.point_2d_to_index(corner)
            if (x, y, eye_z-1) in self.scene_map:   #check body
                clash += index
            if (x, y, eye_z) in self.scene_map:   #check head
                clash += (index<<4)
            clash_points += clash
            index = index << 1
        return clash_points
    
    def _decide_next_move(self, 
                          from_pos: Vector3,
                          to_pos: Vector3):
        if self.clash_points == 0x00:
            self.move_direction = 0x00
            return to_pos
        
        # smooth move
        next_pos = from_pos
        low_clash = self.clash_points & 0x0F
        high_clash = (self.clash_points>>4) & 0x0F
        
        if (low_clash==0x03) and (high_clash&0x0C==0x00):
            next_pos.x = to_pos.x
            self.move_direction = 0x01
        elif (low_clash==0x0C) and (high_clash&0x03==0x00):
            next_pos.x = to_pos.x
            self.move_direction = 0x01
        elif (low_clash==0x06) and (high_clash&0x09==0x00):
            next_pos.y = to_pos.y
            self.move_direction = 0x02
        elif (low_clash==0x09) and (high_clash&0x06==0x00):
            next_pos.y = to_pos.y
            self.move_direction = 0x02
        elif (low_clash&(low_clash-1)==0) and (low_clash|high_clash==low_clash):
            if self.move_direction == 0x01:
                next_pos.x = to_pos.x
            elif self.move_direction == 0x02:
                 next_pos.y = to_pos.y
        else:
            self.move_direction = 0x03
        return next_pos
              
class SceneTracker(object):
    def __init__(self):
        self.scene_map = dict()
        self.live_map = dict()
        self.follow_up = None
        self.fall_down = False
        self.clash_dector = ClashDetector(self.scene_map, self.live_map)
        
    def reload(self, cubes: list):
        self.scene_map.clear()
        self.add_cubes(cubes)
    
    def reload_live_cubes(self, cubes: list):
        self.live_map.clear()
        self.add_live_cubes(cubes)
    
    def move_to(self,
                from_pos: Vector3,
                to_pos: Vector3,
                time: float,
                linked = False):
        if not linked:
            current_pos = self.clash_dector.detect_clash_in_move(from_pos, to_pos)
            if not self.clash_dector.is_clash_with_live_cube(current_pos, time):
                fall_down = self.clash_dector.is_on_air(current_pos)
                return (current_pos, fall_down)
            return (from_pos, False)
        else:
            fall_down = not self.clash_dector.is_land_on_live_cube(to_pos, time)
            return (to_pos, fall_down)
    
    def fly_to(self,
               from_pos: Vector3,
               to_pos: Vector3,
               dir, time: float):
        if self.clash_dector.detect_clash_in_fly(to_pos, dir):
            return (from_pos, ClashType.Static)
        penetration = self.clash_dector.detect_clash_with_live_cube(to_pos, time)
        if penetration is not None:
            next_pos = to_pos - penetration
            if penetration.z > ZERO:
                return (next_pos, ClashType.LivePZ)
            elif penetration.z < -ZERO:
                return (next_pos, ClashType.LiveNZ)
            return (next_pos, ClashType.LiveXY)
        return (to_pos, ClashType.NoClash)

    def add_cubes(self, cubes: list):
        count = len(cubes)
        for i in range(0, count, 6):
            self.add_cube((cubes[i],cubes[i+1],cubes[i+2]))
           
    def add_cube(self, center = (0.0, 0,0, 0.0)):
        center_key = Grid3D.offset_3d_to_index(center)
        self.scene_map[center_key] = True
    
    def remove_cube(self, center = (0.0, 0.0, 0.0)):
        center_key = Grid3D.offset_3d_to_index(center)
        if center_key in self.scene_map:
            del self.scene_map[center_key]
    
    def add_live_cubes(self, cubes: list):
        count = len(cubes)
        for i in range(0, count, 9):
            self.add_live_cube(i//9)
    
    def add_live_cube(self, index):
        cube = LiveCube(index)
        for grid in cube.get_range():
            self.live_map[grid] = index
        
    def reset_eye_position(self, pos):
        return self.clash_dector.reset_eye_position(pos)
    
    def validate_placement(self, center, eye_pos: Vector3):
        return self.clash_dector.validate_placement(center, eye_pos)
              
    def validate_movement(self, 
                          from_center:Vector3, 
                          to_center:Vector3, 
                          action: KeyActions,
                          eye_pos:Vector3):
        if self.clash_dector.is_land_on_cube(eye_pos, from_center):
            if not self.clash_dector.validate_placement(to_center):
                return False
            
            diff = to_center - from_center
            if action == KeyActions.DOWN:
                self.follow_up = diff
                return True
            
            target = eye_pos + diff - Vector3(base_center)
            if not self.clash_dector.validate_placement(target):
                return False
            
            if action == KeyActions.UP:
                self.follow_up = diff
                return True
            
            target.z -= unit_size
            if not self.clash_dector.validate_placement(target):
                return False
            
            self.follow_up = diff
            return True
        return self.clash_dector.validate_placement(to_center, eye_pos)
    
    def validate_remove(self, center, eye_pos: Vector3):
         if self.clash_dector.is_land_on_cube(eye_pos, center):
             self.fall_down = True
        
    @property
    def clashed_cube(self):
        return self.clash_dector.live_cube
    
    
    
        