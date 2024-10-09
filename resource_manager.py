import freetype
import pyglet
from moderngl_window import resources
from moderngl_window.meta import (
    TextureDescription, 
    ProgramDescription,
    DataDescription)
from os import path

Resource_dir = path.normpath(path.join(__file__, '../resources'))

class ResourceManger(object):
    resource_dir = None
    _shaders = {}
    _textures = {}
    _audio = {}

    @classmethod
    def initialize(cls, resource_dir = Resource_dir):
        cls.resource_dir = resource_dir
        resources.register_dir(resource_dir)
        pyglet.resource.path = [path.join(resource_dir, "audio")]

    @classmethod
    def load_all_resources(cls):
        # crosshair shader
        cls._shaders['cross'] = ResourceManger._load_program(
            vertex_shader="shaders/cross.vs",
            fragment_shader="shaders/cross.fs"
        )
        
        # ground shader
        cls._shaders['ground'] = ResourceManger._load_program(
            vertex_shader="shaders/ground.vs",
            fragment_shader="shaders/ground.fs")
        
        # ground picking shader
        cls._shaders['ground_pick'] = ResourceManger._load_program(
            vertex_shader="shaders/ground_pick.vs",
            fragment_shader="shaders/ground_pick.fs")

        # scene shader
        cls._shaders['scene']  = ResourceManger._load_program(
            vertex_shader="shaders/scene.vs",
            fragment_shader="shaders/scene.fs")
        
        # scene_picking shader
        cls._shaders['scene_pick'] = ResourceManger._load_program(
            vertex_shader="shaders/scene_pick.vs",
            fragment_shader="shaders/scene_pick.fs")
        
        # sounds
        cls._audio['solid'] = pyglet.resource.media("solid.wav", False)
        cls._audio['reset'] = pyglet.resource.media("reset.wav", False)
        
    @classmethod
    def get_shader(cls, name):
        return cls._shaders[name]
    
    @classmethod
    def get_texture(cls, name):
        return cls._textures[name]
    
    @classmethod
    def get_audio(cls, name):
        return cls._audio[name]
    
    @classmethod
    def get_screenshot(cls, name):
        return path.join(cls.resource_dir, f"screenshots/{name}.png")
    
    @classmethod
    def _load_font(cls, fontname, height):
        font_path = path.join(cls.resource_dir, "fonts", fontname)
        face = freetype.Face(font_path)
        face.set_pixel_sizes(0, height)
        return face
    
    @classmethod
    def load_data(cls, path: str, kind='text'):
        data = resources.data.load(DataDescription(path=path , kind=kind))
        return data
    
    @classmethod
    def _load_program(cls,
                     vertex_shader=None,
                     fragment_shader=None):
        prog = resources.programs.load(ProgramDescription(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader))
        return prog

    @classmethod
    def _load_texture_2d(cls, path: str):
        texture = resources.textures.load(TextureDescription(path=path))
        return texture
    
    
    
