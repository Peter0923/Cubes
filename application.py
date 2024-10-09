import moderngl as gl
import moderngl_window as glw
from logger import logger
from moderngl_window.conf import settings
from moderngl_window.timers.clock import Timer
from resource_manager import ResourceManger
from scene_builder import SceneBuilder

# Create Window
settings.WINDOW = {
    "class": "moderngl_window.context.pyglet.Window",
    "gl_version": (3, 3),
    "title": "Cubes",
    "size": (1352, 815),
    "fullscreen": False,
    "resizable": False,
    "aspect_ratio": None, 
    "vsync": True
}
window = glw.create_window_from_settings()

# OpenGL context configuration
ctx = window.ctx
ctx.enable(gl.DEPTH_TEST | gl.CULL_FACE)

# Load OpenGL resource
ResourceManger.initialize()
ResourceManger.load_all_resources()

# Init window event handlers
cube_builder = SceneBuilder(window)
window.render_func = getattr(cube_builder, "render")
window.mouse_press_event_func = getattr(cube_builder, "mouse_press")
window.mouse_release_event_func = getattr(cube_builder, "mouse_release")
window.mouse_drag_event_func = getattr(cube_builder, "mouse_drag")
window.mouse_scroll_event_func = getattr(cube_builder, "mouse_scroll")
window.mouse_position_event_func = getattr(cube_builder, "mouse_position")
window.key_event_func = getattr(cube_builder, "key_event")

timer = Timer()
timer.start()

while not window.is_closing:
    current_time, delta = timer.next_frame()
    window.clear(0.2, 0.2, 0.2, 1.0)
    window.render(current_time, delta)
    window.swap_buffers()

_, duration = timer.stop()
window.destroy()

if duration > 0:
    logger.info(
        "Duration: {0:.2f}s @ {1:.2f} FPS".format(
            duration, window.frames / duration))