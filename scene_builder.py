import uuid
from logger import logger
from PIL import Image
from moderngl_window import BaseWindow
from scene_generator import colors
from resource_manager import ResourceManger
from camera import CameraMode, OrbitCamera, WalkCamera
from scene_tracker import SceneTracker, body_height
from cross_render import CrossRender
from ground_render import GroundRender
from cube_render import CubeRender
from pyrr import Matrix44

class SceneBuilder(object):
    enable_build_in_walk = False
    
    def __init__(self, wnd: BaseWindow):
        self.wnd = wnd
        self.ctx = self.wnd.ctx
        self.fbo = self.initializeFramebuffer()
        
        self.tracker = SceneTracker()  
        self.cross = CrossRender(self.ctx, self.wnd.aspect_ratio) 
        self.ground = GroundRender(self.ctx)
        self.scene = CubeRender(self.ctx, self.tracker)
        
        # set projection
        proj = Matrix44.perspective_projection(60.0, self.wnd.aspect_ratio, 0.01, 1000)
        self.ground.set_projection(proj)
        self.scene.set_projection(proj)
        
        # init cameras
        self.orbit_camera = OrbitCamera(wnd, self.tracker)
        self.walk_camera = WalkCamera(wnd, self.tracker)
        self.camera = self.walk_camera
        self.wnd.mouse_exclusivity = True
    
    def initializeFramebuffer(self):
        window_size = self.wnd.size
        fbo = self.ctx.framebuffer((
            self.ctx.texture(window_size, components=4, dtype='f4'),
            self.ctx.texture(window_size, components=4, dtype='f4')),
            self.ctx.depth_renderbuffer(window_size))
        return fbo
    
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
        if key in self.camera.keyMap:
            self.camera.move_state(key, action)
        elif action == keys.ACTION_PRESS:
            if keys.NUMBER_0 <= key <= keys.NUMBER_9:
                self.scene.cube_color = colors[key-keys.NUMBER_0]
            elif key==keys.O:
                self.scene.save()
            elif key==keys.L:
                self.enable_build_in_walk = not self.enable_build_in_walk
                # self.reload()
            elif key==keys.I:
                self.switch_camera()
            elif key==keys.P:
                self.capture_screen()
            
    def mouse_press(self, x: int, y: int, button: int):
        self.building = True
    
    def mouse_release(self, x: int, y: int, button: int):
        if not self.building:
            return
        
        self.fbo.use()
        if button == 1:
            if self.camera.mode == CameraMode.Orbit:
                self.scene.add_cube(x, self.wnd.height-y)
            elif self.enable_build_in_walk:
                self.scene.add_cube(self.wnd.width/2, self.wnd.height/2, self.camera.position)
        elif button == 2:
            if self.camera.mode == CameraMode.Orbit:
                self.scene.remove_cube(x, self.wnd.height-y)
            elif self.enable_build_in_walk:
                self.scene.remove_cube(self.wnd.width/2, self.wnd.height/2)
            
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
        lookat = self.camera.look_and_move(frame_time)
        self.ground.update_view(lookat)
        self.scene.update_view(lookat)
        
        self.fbo.use()
        self.fbo.clear(-1, -1, -1, -1)
        self.ground.render_picker()
        self.scene.render_picker()
        
        self.ctx.screen.use()
        if self.camera.mode == CameraMode.Walk:
            self.cross.render()
        self.ground.render()
        self.scene.render()
    
    def capture_screen(self):
        file_name = uuid.uuid4()
        screen = Image.frombytes('RGB', 
                                self.ctx.screen.size, 
                                self.ctx.screen.read(), 
                                'raw', 'RGB', 0, -1)
        screen.save(ResourceManger.get_screenshot(file_name))
    
    
    # def log_info(self):
    #     self.tracker.log_info()
        
    