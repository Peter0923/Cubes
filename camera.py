from enum import Enum
from math import cos, sin, radians
from pyrr import Matrix44, Vector3, vector3, vector
from resource_manager import ResourceManger
from scene_generator import SceneGenerator, KeyActions, ground_width, unit_size
from scene_tracker import SceneTracker, ClashType, body_height
from scene_linker import Linkage

STILL = 0
POSITIVE = 1
NEGATIVE = -1

# Orbit settings
zoom_init = ground_width * 2.2
zoom_max = ground_width * 7

# Walk settings
init_position = (0.0, 0.0, body_height)

class CameraMode(Enum):
    Orbit = 0
    Walk = 1

class Camera(object):
    def __init__(self,
                 mode: CameraMode, 
                 tracker: SceneTracker):
        self.mode = mode
        self.tracker = tracker
        self.move_action = None
        self.reset_sound = ResourceManger.get_audio('reset')
    
    def move_state(self, action: KeyActions, key_pressed):
        self.move_action = action if key_pressed else None
        match action:
            case KeyActions.FORWARD:
                if key_pressed:
                    self.ydir = POSITIVE
                elif self.ydir == POSITIVE:
                    self.ydir = STILL
            case KeyActions.BACKWARD:
                if key_pressed:
                    self.ydir = NEGATIVE
                elif self.ydir == NEGATIVE:
                    self.ydir = STILL
            case KeyActions.LEFT:
                if key_pressed:
                    self.xdir = NEGATIVE
                elif self.xdir == NEGATIVE:
                    self.xdir = STILL
            case KeyActions.RIGHT:
                if key_pressed:
                    self.xdir = POSITIVE
                elif self.xdir == POSITIVE:
                    self.xdir = STILL
    
    def resume_move(self):
        if self.move_action is not None:
            match self.move_action:
                case KeyActions.FORWARD:
                    self.ydir = POSITIVE
                case KeyActions.BACKWARD:
                    self.ydir = NEGATIVE
                case KeyActions.LEFT:
                    self.xdir = NEGATIVE
                case KeyActions.RIGHT:
                    self.xdir = POSITIVE
        
# Orbit camera
class OrbitCamera(Camera):
    def __init__(self, tracker: SceneTracker):
        super().__init__(CameraMode.Orbit, tracker)
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
        
    def look_and_move(self, t, dt):
        if self.xdir != STILL:
            self.target += self.right * self.xdir * self.velocity * dt
        if self.ydir != STILL:
            self.target += self.dir * self.ydir * self.velocity * dt
        if self.zdir != STILL:
            self.target += self.up * self.zdir * self.velocity * dt
        self.position = self.target + self.eye 
        
        return Matrix44.look_at(
            self.position,
            self.target,  #what to look at
            self.up)  #camera up direction (change for rolling the camera)
 
    def move_state(self, action: KeyActions, key_pressed):
        match action:
            case KeyActions.FORWARD | KeyActions.BACKWARD | KeyActions.LEFT | KeyActions.RIGHT:
                super().move_state(action, key_pressed)
            case KeyActions.UP:
                if key_pressed:
                    self.zdir = POSITIVE
                elif self.zdir == POSITIVE:
                    self.zdir = STILL
            case KeyActions.DOWN:
                if key_pressed:
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
    def __init__(self, tracker:SceneTracker):
        super().__init__(CameraMode.Walk, tracker)
        self.velocity = 4.0
        self.mouse_sensitivity = 0.05
        self.max_look_up = 30
        self.max_look_down = -85
        self.max_fly_time = 1.0    #seconds
        self.link = Linkage()
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
        self.fly_time = 0.0
        self.link.end_link()
    
    def reset_eye(self, keep_eye = False):
        if not keep_eye:
            self.reset_sound.play()
            self.position = self.tracker.reset_eye_position(Vector3(init_position))
        else:
            self.position = self.tracker.reset_eye_position(self.position)
            if self.position is None:
                self.reset_eye()
        
    def look_and_move(self, t, dt):
        if self.link.linked:
            self.position = self.link.get_linked_eye(t)
        elif self.tracker.follow_up is not None:
            self.position += self.tracker.follow_up
            self.tracker.follow_up = None
        elif self.tracker.fall_down:
            self.zdir = NEGATIVE
            self.tracker.fall_down = False
            
        if self.xdir!=STILL or self.ydir!=STILL or self.zdir!=STILL:
            next_pos = self.position.copy()
            if self.xdir != STILL:
                next_pos += self.right * self.xdir * self.velocity * dt
            if self.ydir != STILL:
                next_pos += self.front * self.ydir * self.velocity * dt

            if self.zdir == STILL:  #moving
                self.move_to(next_pos, t)  
            else:    #flying
                self.fly_to(next_pos, t, dt) 
            if (not SceneGenerator.is_in_grid(self.position.xy)) and (self.position.z<0):
                self.reset()   #back to origin
            
        return Matrix44.look_at(
            self.position,
            self.position + self.dir,
            self.up)
    
    def move_to(self, next_pos, t):
        next_pos, fall_down = self.tracker.move_to(
                self.position, 
                next_pos, t, 
                self.link.linked)
        if self.link.linked:
            offset = next_pos - self.position
            self.link.update_offset(offset)
        self.position = next_pos 
        if fall_down:
            self.zdir = NEGATIVE
            self.link.end_link()
    
    def fly_to(self, next_pos, t, dt):
        next_pos += self.up * self.zdir * self.velocity * dt
        fly_dir = 0 if (self.xdir!=STILL or self.ydir!=STILL) else self.zdir
        self.position, clash_type = self.tracker.fly_to(self.position, next_pos, fly_dir, t)
        if clash_type != ClashType.NoClash:
            if fly_dir == 0:
                self.xdir = STILL 
                self.ydir = STILL  
            elif self.zdir == POSITIVE:
                self.zdir = NEGATIVE
            elif self.zdir == NEGATIVE and clash_type.value <= 2:
                self.zdir = STILL
                if clash_type == ClashType.LiveNZ:
                    self.link.start_link(self.tracker.clashed_cube, self.position, t)
                super().resume_move()
        
        # update flying up time
        if self.zdir == POSITIVE:
            self.fly_time += dt
            if self.fly_time >= self.max_fly_time:
                self.zdir = NEGATIVE
    
    def move_state(self, action: KeyActions, key_pressed):
        match action:
            case KeyActions.FORWARD | KeyActions.BACKWARD | KeyActions.LEFT | KeyActions.RIGHT:
                super().move_state(action, key_pressed)
            case KeyActions.JUMP:
                if key_pressed:
                    self.zdir = POSITIVE
                    self.fly_time = 0.0
                    self.link.end_link()
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
        
            
            
                
        