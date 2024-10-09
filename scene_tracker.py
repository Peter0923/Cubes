from logger import logger
from pyrr import Vector3
from scene_generator import SceneGenerator, unit_size, half_unit, base_center
from resource_manager import ResourceManger

near_zero = 0.1
body_height = 1.5 * unit_size  #not higher than 2 units
body_clash = 0.1 * unit_size

class ClashDetector(object):
    def __init__(self, scene_map):
        self.scene_map = scene_map
        self.clash_points = 0x00
        self.move_direction = 0x00
        self.land_sound = ResourceManger.get_audio('solid')
    
    def detect_clash_in_move(self,
                             from_pos: Vector3,
                             to_pos: Vector3):
        self.clash_points = self._get_clash_points(to_pos)
        current_pos = self._decide_next_move(from_pos, to_pos)
        fall_down = self._is_on_air(current_pos)
        return (current_pos, fall_down)
     
    def detect_clash_in_fly(self, 
                            to_pos: Vector3,
                            dir):   #1(Up), 0(Free), -1(Down)
        # land on ground
        body_z = self._get_all_z_index(to_pos.z)
        if body_z[2]<0 and SceneGenerator.is_in_grid(to_pos.xy):    
            self.land_sound.play()
            return True
        
        # decide check points
        if dir == 1:
            body_z = body_z[:1]
        elif dir == -1:
            body_z = body_z[2:]
        elif body_z[1] == body_z[2]:
            body_z = body_z[:2]
        
        corners = self._get_all_xy_index(to_pos)
        for (x, y) in corners:
            for z in body_z:
                if (x, y, z) in self.scene_map:
                    return True
        return False
            
    def get_eye_position(self, eye_pos: Vector3):
        eye_z = eye_pos.z
        x, y, z = self._point_3d_to_index(eye_pos.tolist())
        while ((x, y, z) in self.scene_map) or ((x, y, z-1) in self.scene_map): 
            z += 1
            eye_z += unit_size
        while z>1 and ((x, y, z-2) not in self.scene_map):
            z -= 1
            eye_z -= unit_size
        if z<=1 and (not SceneGenerator.is_in_grid(eye_pos.xy)):
            return None  
        return Vector3([eye_pos.x, eye_pos.y, eye_z])
          
    def _get_clash_points(self, pos: Vector3):
        index = 0x01
        clash_points = 0x00
        corners = self._get_box_2d(pos)
        eye_z = int(pos.z / unit_size)
        for corner in corners:
            clash = 0x00
            x, y = self._point_2d_to_index(corner)
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
    
    def _is_on_air(self, eye_pos: Vector3):
        foot = eye_pos.z - body_height
        if (foot<base_center[2]) and (SceneGenerator.is_in_grid(eye_pos.xy)):
            return False
        
        foot -= half_unit
        z_index = int(foot / unit_size)
        corners = self._get_box_2d(eye_pos)
        for corner in corners:
            x, y = self._point_2d_to_index(corner)
            if (x, y, z_index) in self.scene_map:
                return False
        return True
        
    @classmethod 
    def is_clash_with_eye(cls, center, eye_pos: Vector3):
        cube_index = cls._offset_3d_to_index(center)
        corners = cls._get_box_2d(eye_pos)
        eye_z = int(eye_pos.z / unit_size)
        for corner in corners:
            x, y = cls._point_2d_to_index(corner)
            if (x, y, eye_z-1) == cube_index:   #check leg
                return True
            if (x, y, eye_z) == cube_index:   #check head
                return True
        return False
    
    @classmethod
    def _get_all_z_index(cls, eye_z_pos):
        eye_dz = eye_z_pos + body_clash - base_center[2]
        leg_dz = eye_z_pos - unit_size - base_center[2]
        foot_dz = eye_z_pos - body_height - base_center[2]
        return cls._offsets_to_index((eye_dz, leg_dz, foot_dz))
    
    @classmethod
    def _get_all_xy_index(cls, pos: Vector3):
        left = pos.x - body_clash - base_center[0] 
        right = pos.x + body_clash - base_center[0]
        bottom = pos.y - body_clash - base_center[1]
        top = pos.y + body_clash - base_center[1]
        corners = cls._offsets_to_index((left, right, bottom, top))
        return ((corners[0], corners[3]),
                (corners[1], corners[3]),
                (corners[1], corners[2]),
                (corners[0], corners[2]))
        
    @classmethod
    def _get_box_2d(cls, pos: Vector3):
        left = pos.x - body_clash
        right = pos.x + body_clash
        bottom = pos.y - body_clash
        top = pos.y + body_clash
        corners = ((left, top), (right, top), (right, bottom), (left, bottom))
        return corners
    
    @classmethod
    def _point_2d_to_index(cls, point):
        dx = point[0] - base_center[0]
        dy = point[1] - base_center[1]
        index_x = int((dx+half_unit)/unit_size) if dx>=0 else int((dx-half_unit)/unit_size)
        index_y = int((dy+half_unit)/unit_size) if dy>=0 else int((dy-half_unit)/unit_size)
        return (index_x, index_y)
    
    @classmethod
    def _point_3d_to_index(cls, point):
        dx = point[0] - base_center[0]
        dy = point[1] - base_center[1]
        dz = point[2] - base_center[2]
        return cls._offset_3d_to_index((dx, dy, dz))
          
    @classmethod
    def _offset_3d_to_index(cls, offset):
        index_x = int((offset[0]+half_unit)/unit_size) if offset[0]>=0 else int((offset[0]-half_unit)/unit_size)
        index_y = int((offset[1]+half_unit)/unit_size) if offset[1]>=0 else int((offset[1]-half_unit)/unit_size)
        index_z = int((offset[2]+half_unit)/unit_size) if offset[2]>=0 else int((offset[2]-half_unit)/unit_size)
        return (index_x, index_y, index_z)
    
    @classmethod
    def _offsets_to_index(cls, offsets):
        all_index = []
        for offset in offsets:
            index = int((offset+half_unit)/unit_size) if offset>=0 else int((offset-half_unit)/unit_size)
            all_index.append(index)
        return all_index
              
class SceneTracker(object):
    def __init__(self):
        self.scene_map = dict()
        self.clash_dector = ClashDetector(self.scene_map)
        
    def reload(self, cubes: list):
        self.scene_map.clear()
        self.add_cubes(cubes)
    
    def move_to(self,
                from_pos: Vector3,
                to_pos: Vector3):
        return self.clash_dector.detect_clash_in_move(from_pos, to_pos)
        
    def fly_to(self,
               from_pos: Vector3,
               to_pos: Vector3,
               dir = 0):
        return not self.clash_dector.detect_clash_in_fly(to_pos, dir)
    
    def add_cubes(self, cubes: list):
        count = len(cubes)
        for i in range(0, count, 6):
            self.add_cube((cubes[i],cubes[i+1],cubes[i+2]))
           
    def add_cube(self, center = (0.0, 0,0, 0.0)):
        center_key = self.clash_dector._offset_3d_to_index(center)
        self.scene_map[center_key] = True
    
    def remove_cube(self, center = (0.0, 0.0, 0.0)):
        center_key = self.clash_dector._offset_3d_to_index(center)
        if center_key in self.scene_map:
            del self.scene_map[center_key]
    
    def get_eye_position(self, pos):
        return self.clash_dector.get_eye_position(pos)
        
    @classmethod
    def is_clashed(cls, center, eye_pos: Vector3):
        return ClashDetector.is_clash_with_eye(center, eye_pos)
    
    # def log_info(self):
    #     logger.info(
    #         "current pos: ({:.2f}, {:.2f}, {:.2f})".format(x, y, z))
        
        
    
    
            
    
        
    
        
        
        
        
        