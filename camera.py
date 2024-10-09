import enum
from collections import namedtuple
from math import cos, sin, radians
from pyrr import Matrix44, Vector3, vector3, vector
from moderngl_window import BaseWindow
from moderngl_window.context.base.keys import BaseKeys
from resource_manager import ResourceManger
from scene_generator import SceneGenerator, ground_width
from scene_tracker import SceneTracker, body_height

STILL = 0
POSITIVE = 1
NEGATIVE = -1

# Orbit settings
zoom_init = ground_width * 2.2
zoom_max = ground_width * 7

# Walk settings
init_position = (0.0, 0.0, body_height)

class CameraMode(enum.Enum):
    Orbit = 0
    Walk = 1

WalkKeys = namedtuple("WalkKeys", ["FORWARD", "BACKWARD", "LEFT", "RIGHT", "UP"])
OrbitKeys = namedtuple("OrbitKeys", ["FORWARD", "BACKWARD", "LEFT", "RIGHT", "UP", "DOWN"])

class Camera(object):
    def __init__(self,
                 wnd: BaseWindow,
                 mode: CameraMode, 
                 tracker: SceneTracker):
        self.wnd = wnd
        self.mode = mode
        if self.mode == CameraMode.Walk:
            move_keys = WalkKeys(
                FORWARD = wnd.keys.W,
                BACKWARD = wnd.keys.S,
                LEFT = wnd.keys.A,
                RIGHT = wnd.keys.D,
                UP = wnd.keys.SPACE)
        else:
            move_keys = OrbitKeys(
                FORWARD = wnd.keys.W,
                BACKWARD = wnd.keys.S,
                LEFT = wnd.keys.A,
                RIGHT = wnd.keys.D,
                UP = wnd.keys.UP,
                DOWN = wnd.keys.DOWN)
        self.keyMap = move_keys
        self.tracker = tracker
        self.reset_sound = ResourceManger.get_audio('reset')
        
# Orbit camera
class OrbitCamera(Camera):
    def __init__(self, wnd, tracker: SceneTracker):
        super().__init__(wnd, CameraMode.Orbit, tracker)
        self.velocity = 5.0
        self.mouse_sensitivity = 1.0
        self.reset()
    
    def reset(self): 
        self.yaw = -90.0
        self.pitch = 20.0
        self.radius = zoom_init
        
        self.target = Vector3([0.0, 0.0, 0.0])
        self.up = Vector3([0.0, 0.0, 1.0])
        self.update_eye()
        
        self.xdir = STILL
        self.ydir = STILL
        self.zdir = STILL
    
    @property
    def position(self):
        return self.target + self.eye
        
    def look_and_move(self, dt): 
        if self.xdir != STILL:
            self.target += self.right * self.xdir * self.velocity * dt
        if self.ydir != STILL:
            self.target += self.dir * self.ydir * self.velocity * dt
        if self.zdir != STILL:
            self.target += self.up * self.zdir * self.velocity * dt
        
        return Matrix44.look_at(
            self.target + self.eye,
            self.target,  #what to look at
            self.up)  #camera up direction (change for rolling the camera)
    
    def move_state(self, key, action):
        if key == self.keyMap.FORWARD:
            if action == BaseKeys.ACTION_PRESS:
                self.ydir = POSITIVE
            elif self.ydir == POSITIVE:
                self.ydir = STILL
        elif key == self.keyMap.BACKWARD:
            if action == BaseKeys.ACTION_PRESS:
                self.ydir = NEGATIVE
            elif self.ydir == NEGATIVE:
                self.ydir = STILL
        elif key == self.keyMap.LEFT:
            if action == BaseKeys.ACTION_PRESS:
                self.xdir = NEGATIVE
            elif self.xdir == NEGATIVE:
                self.xdir = STILL
        elif key == self.keyMap.RIGHT:
            if action == BaseKeys.ACTION_PRESS:
                self.xdir = POSITIVE
            elif self.xdir == POSITIVE:
                self.xdir = STILL
        elif key == self.keyMap.UP:
            if action == BaseKeys.ACTION_PRESS:
                self.zdir = POSITIVE
            elif self.zdir == POSITIVE:
                self.zdir = STILL
        elif key == self.keyMap.DOWN:
            if action == BaseKeys.ACTION_PRESS:
                self.zdir = NEGATIVE
            elif self.zdir == NEGATIVE:
                self.zdir = STILL
            
    def rot_state(self, dx, dy):
        self.yaw -= dx * self.mouse_sensitivity / 10.0
        self.pitch += dy * self.mouse_sensitivity / 10.0
        self.pitch = max(min(self.pitch, 89), 0)
        self.update_eye()
    
    def zoom_state(self, offset):
        self.radius -= offset * self.mouse_sensitivity / 5.0
        self.radius = max(min(self.radius, zoom_max), 1)
        self.update_eye()
    
    def update_eye(self):
        self.eye = Vector3([0.0, 0.0, 0.0])
        self.eye.x = cos(radians(self.yaw)) * cos(radians(self.pitch)) * self.radius
        self.eye.y = sin(radians(self.yaw)) * cos(radians(self.pitch)) * self.radius
        self.eye.z = sin(radians(self.pitch)) * self.radius  
        # self.dir = vector.normalise(-self.eye)
        self.dir = vector.normalise(Vector3([-self.eye.x, -self.eye.y, 0.0]))
        self.right = vector.normalise(vector3.cross(self.dir, self.up))
        # self.up = vector.normalise(vector3.cross(self.right, self.dir))
        

# Walk camera
class WalkCamera(Camera):
    def __init__(self, 
                 wnd, 
                 tracker:SceneTracker):
        super().__init__(wnd, CameraMode.Walk, tracker)
        self.velocity = 4.0
        self.mouse_sensitivity = 0.05
        self.max_look_up = 30
        self.max_look_down = -60
        self.max_fly_time = 1      #seconds
        self.reset()
        
    def reset(self):
        self.reset_eye()
        self.up = Vector3([0.0, 0.0, 1.0])
        
        self.yaw = 90.0
        self.pitch = 0.0
        self.update_target()
        
        self.xdir = STILL
        self.ydir = STILL
        self.zdir = STILL
        self.fly_time = 0
    
    def reset_eye(self, keep_eye = False):
        if not keep_eye:
            self.reset_sound.play()
            self.position = self.tracker.get_eye_position(Vector3(init_position))
        else:
            self.position = self.tracker.get_eye_position(self.position)
            if self.position is None:
                self.reset_eye()
        
    def look_and_move(self, dt):
        if self.xdir!=STILL or self.ydir!=STILL or self.zdir!=STILL:
            self.move_one_step(dt)
            if (not SceneGenerator.is_in_grid(self.position.xy)) and (self.position.z<0):
                self.reset()   #back to origin
            
        return Matrix44.look_at(
            self.position,
            self.position + self.dir,
            self.up)
    
    def move_one_step(self, dt):
        next_pos = self.position.copy()
        if self.xdir != STILL:
            next_pos += self.right * self.xdir * self.velocity * dt
        if self.ydir != STILL:
            next_pos += self.front * self.ydir * self.velocity * dt
        
        if self.zdir == STILL:  #moving 
            self.position, fall_down = self.tracker.move_to(self.position, next_pos)
            if fall_down:
                self.zdir = NEGATIVE
        else:    #flying
            next_pos += self.up * self.zdir * self.velocity * dt
            fly_dir = 0 if (self.xdir!=STILL or self.ydir!=STILL) else self.zdir
            if self.tracker.fly_to(self.position, next_pos, fly_dir):
                self.position = next_pos
            elif fly_dir == 0:
                self.xdir = STILL
                self.ydir = STILL   
            elif self.zdir == POSITIVE:
                self.zdir = NEGATIVE
            elif self.zdir == NEGATIVE:
                self.zdir = STILL
                self.resume_move()
            
            # update flying up time
            if self.zdir == POSITIVE:
                self.fly_time += dt
                if self.fly_time >= self.max_fly_time:
                    self.zdir = NEGATIVE
    
    def move_state(self, key, action):
        if key == self.keyMap.FORWARD:
            if action == BaseKeys.ACTION_PRESS:
                self.ydir = POSITIVE
            elif self.ydir == POSITIVE:
                self.ydir = STILL
        elif key == self.keyMap.BACKWARD:
            if action == BaseKeys.ACTION_PRESS:
                self.ydir = NEGATIVE
            elif self.ydir == NEGATIVE:
                self.ydir = STILL
        elif key == self.keyMap.LEFT:
            if action == BaseKeys.ACTION_PRESS:
                self.xdir = NEGATIVE
            elif self.xdir == NEGATIVE:
                self.xdir = STILL
        elif key == self.keyMap.RIGHT:
            if action == BaseKeys.ACTION_PRESS:
                self.xdir = POSITIVE
            elif self.xdir == POSITIVE:
                self.xdir = STILL
        elif key == self.keyMap.UP:
            if action == BaseKeys.ACTION_PRESS:
                self.zdir = POSITIVE
                self.fly_time = 0
            elif self.zdir == POSITIVE:
                self.zdir = NEGATIVE
    
    def rot_state(self, dx, dy):
        self.yaw -= dx * self.mouse_sensitivity
        self.pitch -= dy * self.mouse_sensitivity * 0.5
        self.pitch = max(min(self.pitch, self.max_look_up), self.max_look_down)
        self.update_target()
    
    def update_target(self):
        self.dir = Vector3([0.0, 0.0, 0.0])
        self.dir.x = cos(radians(self.yaw)) * cos(radians(self.pitch))
        self.dir.y = sin(radians(self.yaw)) * cos(radians(self.pitch))
        self.dir.z = sin(radians(self.pitch))    
        self.front = vector.normalise(Vector3([self.dir.x, self.dir.y, 0.0]))
        self.right = vector.normalise(vector3.cross(self.front, self.up))
    
    def resume_move(self):
        if self.wnd.is_key_pressed(self.keyMap.FORWARD):
            self.ydir = POSITIVE
        elif self.wnd.is_key_pressed(self.keyMap.BACKWARD):
            self.ydir = NEGATIVE
        if self.wnd.is_key_pressed(self.keyMap.LEFT):
            self.xdir = NEGATIVE
        elif self.wnd.is_key_pressed(self.keyMap.RIGHT):
            self.xdir = POSITIVE
        
            
            
                
        