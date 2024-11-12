import uuid
import enum
from PIL import Image
from moderngl_window import BaseWindow
from scene_generator import colors, KeyActions
from resource_manager import ResourceManger
from camera import CameraMode, OrbitCamera, WalkCamera
from scene_tracker import SceneTracker
from cross_render import CrossRender
from ground_render import GroundRender
from cube_render import CubeRender
from live_render import LiveCubeRender
from pyrr import Matrix44

class MoveMode(enum.Enum):
    Camera = 0
    Cube = 1
    
class SceneBuilder(object):
    move_mode = MoveMode.Camera
      
    def __init__(self, wnd: BaseWindow):
        self.wnd = wnd
        self.ctx = self.wnd.ctx
        self.fbo = self.initializeFramebuffer()
        
        self.tracker = SceneTracker()  
        self.cross = CrossRender(self.ctx, self.wnd.aspect_ratio) 
        self.ground = GroundRender(self.ctx)
        self.scene = CubeRender(self.ctx, self.tracker)
        self.live_cubes = LiveCubeRender(self.ctx, self.tracker)
        
        # set projection
        proj = Matrix44.perspective_projection(60.0, self.wnd.aspect_ratio, 0.01, 1000)
        self.ground.set_projection(proj)
        self.scene.set_projection(proj)
        self.live_cubes.set_projection(proj)
        
        # init cameras
        self.orbit_camera = OrbitCamera(self.tracker)
        self.walk_camera = WalkCamera(self.tracker)
        self.camera = self.walk_camera
        self.wnd.mouse_exclusivity = True
        
        # init key action mappings
        self.initialize_key_actions()
    
    def initializeFramebuffer(self):
        window_size = self.wnd.size
        fbo = self.ctx.framebuffer((
            self.ctx.texture(window_size, components=4, dtype='f4'),
            self.ctx.texture(window_size, components=4, dtype='f4')),
            self.ctx.depth_renderbuffer(window_size))
        return fbo
    
    def initialize_key_actions(self):
        keys = self.wnd.keys
        self.key_map = {
            keys.W: KeyActions.FORWARD,
            keys.S: KeyActions.BACKWARD,
            keys.A: KeyActions.LEFT,
            keys.D: KeyActions.RIGHT,
            keys.SPACE: KeyActions.JUMP,
            keys.UP: KeyActions.UP,
            keys.DOWN: KeyActions.DOWN
            }
    
    # reload scene from data file
    def reload(self, filename = "cubes0"):
        self.scene.reload(filename)
        self.camera.reset()

    def switch_camera(self):
        if self.camera.mode == CameraMode.Orbit:
            self.camera = self.walk_camera
            self.wnd.mouse_exclusivity = True
            self.camera.reset_eye(True)
        else:
            self.camera = self.orbit_camera
            self.wnd.mouse_exclusivity = False
            self.camera.reset()
    
    def key_event(self, key, action, modifiers):
        keys = self.wnd.keys
        key_pressed = (action == keys.ACTION_PRESS)
        if key in self.key_map:
            if self.move_mode == MoveMode.Camera:   #move camera
                self.camera.move_state(self.key_map[key], key_pressed)
            elif key_pressed:   #move object
                self.scene.move_step(self.key_map[key], self.camera.position, self.camera.dir)
        elif key_pressed:
            if keys.NUMBER_0 <= key <= keys.NUMBER_9:
                self.scene.cube_color = colors[key-keys.NUMBER_0]
            elif key == keys.I:
                self.switch_camera()
            elif key == keys.O:
                self.scene.save()
            elif key == keys.P:
                self.capture_screen()
            elif key == keys.M:
                self.move_mode = MoveMode(1 - self.move_mode.value)
            
    def mouse_press(self, x: int, y: int, button: int):
        self.building = True
    
    def mouse_release(self, x: int, y: int, button: int):
        if not self.building:
            return
        
        if self.camera.mode == CameraMode.Orbit:
            target_x, target_y = x, self.wnd.height-y
        else:
            target_x, target_y = self.wnd.width/2, self.wnd.height/2
        
        self.fbo.use()
        if button == 1:
            if self.move_mode == MoveMode.Camera:
                self.scene.add_cube(target_x, target_y, self.camera.position)
            else:
                self.scene.select_cube(target_x, target_y)
        elif button == 2:
            self.scene.remove_cube(target_x, target_y, self.camera.position)
               
    def mouse_drag(self, x: int, y: int, dx: int, dy: int):
        self.building = False
        if self.camera.mode == CameraMode.Orbit:
            self.camera.rot_state(dx, dy)
    
    def mouse_scroll(self, x_offset: float, y_offset: float):
        self.building = False
        if self.camera.mode == CameraMode.Orbit:
            self.camera.zoom_state(y_offset)
    
    def mouse_position(self, x: int, y: int, dx, dy):
        self.building = False
        if self.camera.mode == CameraMode.Walk:
            self.camera.rot_state(dx, dy)
        
    def render(self, time, frame_time):
        lookat = self.camera.look_and_move(time, frame_time)
        self.ground.update_view(lookat)
        self.scene.update_view(lookat)
        self.live_cubes.update_view(lookat)
        self.live_cubes.update_time(time)
        
        
        self.fbo.use()
        self.fbo.clear(-1, -1, -1, -1)
        self.ground.render_picker()
        self.scene.render_picker()
        
        self.ctx.screen.use()
        if self.camera.mode == CameraMode.Walk:
            self.cross.render()
        self.ground.render()
        self.scene.render()
        self.live_cubes.render()
    
    def capture_screen(self):
        file_name = uuid.uuid4()
        screen = Image.frombytes('RGB', 
                                self.ctx.screen.size, 
                                self.ctx.screen.read(), 
                                'raw', 'RGB', 0, -1)
        screen.save(ResourceManger.get_screenshot(file_name))
    
    
    # def log_info(self):
    #     self.tracker.log_info()
        
    