import numpy
from OpenGL import GL
import moderngl as gl
from moderngl_window import BaseWindow
from pyrr import Matrix44, Vector3
from logger import logger
from scene_generator import KeyActions, unit_size
from resource_manager import ResourceManger
from scene_generator import SceneGenerator
from scene_tracker import SceneTracker
from scene_objects import SceneObjects

cube_max_number = 10000
cube_face_map = {0: (0, 0, unit_size), 1: (unit_size, 0, 0), 
                 2: (0, -unit_size, 0), 3: (-unit_size, 0, 0), 
                 4: (0, 0, -unit_size), 5: (0, unit_size, 0)}

class CubeRender(object):
    def __init__(self,
                 ctx: gl.Context,
                 tracker: SceneTracker):
        self.ctx = ctx
        self.tracker = tracker
        self.selection = None  
        self.cubes = SceneObjects.cubes  
        self.init_scene()
        self.init_picker()
        self.init_move_map()
        
    def init_scene(self):
        cube_normals = self.ctx.buffer(SceneGenerator.cube_normals()) 
        self.cube_pos = self.ctx.buffer(SceneGenerator.cube())
        self.cube_color = None
        
        # self.cubes.extend(SceneGenerator.gen_cube_instances_0())
        self.cubes.extend(SceneGenerator.load_cubes())
        self.tracker.reload(self.cubes)
            
        self.vbo = self.ctx.buffer(reserve = cube_max_number*24)
        self.vbo.write(numpy.array(self.cubes).astype('f4'))
        
        self.prog = ResourceManger.get_shader('scene')
        self.vao = self.ctx.vertex_array(
            self.prog, [
                (self.cube_pos, '3f /v', 'in_vert'),
                (cube_normals, '3f /v', 'in_normal'),
                (self.vbo, '3f 3f /i', 'in_offset', 'in_color')
            ])
    
    def init_picker(self):
        self.prog_pick = ResourceManger.get_shader('scene_pick')
        self.vao_pick = self.ctx.vertex_array(
            self.prog_pick, [
                (self.cube_pos, '3f /v', 'in_vert'),
                (self.vbo, '3f 12x /i', 'in_offset')
            ])
    
    def init_move_map(self):
        self.cube_move_map = {
            KeyActions.FORWARD: lambda front:front,
            KeyActions.BACKWARD: lambda front:-front,
            KeyActions.LEFT: lambda front:Vector3([-front.y, front.x, front.z]),
            KeyActions.RIGHT: lambda front:Vector3([front.y, -front.x, front.z]),
            KeyActions.UP: lambda front: Vector3([0, 0, 1]),
            KeyActions.DOWN: lambda front: Vector3([0, 0, -1])
            }
        
        
    def reload(self, filename = "cubes0"):
        self.cubes.clear()
        self.vbo.clear()
        if filename:
            self.cubes.extend(SceneGenerator.load_cubes(filename))
            self.vbo.write(numpy.array(self.cubes).astype('f4'))
        self.tracker.reload(self.cubes)
    
    def save(self, filename = "cubes0"):
        SceneGenerator.save_cubes(self.cubes, filename)
     
    def set_projection(self, proj: Matrix44):
        self.prog['proj'].write(proj.astype('f4'))
        self.prog_pick['proj'].write(proj.astype('f4'))
        
    def update_view(self, mv: Matrix44):
        self.prog['mv'].write(mv.astype('f4'))
        self.prog_pick['mv'].write(mv.astype('f4'))
    
    def add_cube(self, x, y, eye):
        if self.cube_number == cube_max_number:
            logger.warning(f"Reached the maximum number {cube_max_number}!")
            return
        
        GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
        pixel = GL.glReadPixels(x, y, 1, 1, GL.GL_RGBA, GL.GL_FLOAT)
        data = pixel[0][0]
        face_id = int(data[3])
        if face_id >= 0:
            pos = (data[0] + cube_face_map[face_id][0], 
                   data[1] + cube_face_map[face_id][1], 
                   data[2] + cube_face_map[face_id][2])
            
            if not self.tracker.validate_placement(pos, eye):
                return
            
            color = self.cube_color
            if color is None:
                color = (numpy.random.uniform(0,1),
                         numpy.random.uniform(0,1),
                         numpy.random.uniform(0,1))
                  
            new_cube = [pos[0], pos[1], pos[2], color[0], color[1], color[2]]
            self.cubes.extend(new_cube)
            self.vbo.write(numpy.array(new_cube).astype('f4'), 24*(self.cube_number-1))
            self.tracker.add_cube(pos)
    
    def remove_cube(self, x, y, eye):
        if self.cube_number <= 0:
            logger.warning("No cubes in the scene!")
            return
        
        GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT1)
        data = GL.glReadPixels(x, y, 1, 1, GL.GL_RED, GL.GL_FLOAT)
        id = int(data[0][0])
        if id >= 0:
            del_cube = self.cubes[6*id : 6*id+3]
            del self.cubes[6*id : 6*(id+1)]
            self.vbo.write(numpy.array(self.cubes).astype('f4'))
            self.tracker.remove_cube(del_cube)
            self.tracker.validate_remove(del_cube, eye)
            self.selection = None
    
    def select_cube(self, x, y):
        if self.cube_number <= 0:
            logger.warning("No cubes in the scene!")
            return False
        
        GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT1)
        data = GL.glReadPixels(x, y, 1, 1, GL.GL_RED, GL.GL_FLOAT)
        id = int(data[0][0])
        if id >= 0:
            self.cubes[6*id+3] = 1.0 - self.cubes[6*id+3]
            self.cubes[6*id+4] = 1.0 - self.cubes[6*id+4]
            self.cubes[6*id+5] = 1.0 - self.cubes[6*id+5]
            highlight = numpy.array(self.cubes[6*id+3 : 6*id+6]).astype('f4')
            self.vbo.write(highlight, 24*id+12)
            self.selection = id
            return True
        return False
    
    def move_step(self, action: KeyActions, eye, front):
        id = self.selection
        if (id is None) or (action not in self.cube_move_map):
            return
        
        old_pos = Vector3(self.cubes[6*id : 6*id+3])
        move_dir = self.decide_move_dir(action, front)
        new_pos = old_pos + move_dir
        
        if self.tracker.validate_movement(old_pos, new_pos, eye):
            self.cubes[6*id] = new_pos[0]
            self.cubes[6*id+1] = new_pos[1]
            self.cubes[6*id+2] = new_pos[2]
            self.vbo.write(numpy.array(new_pos).astype('f4'), 24*id)
            self.tracker.remove_cube(old_pos)
            self.tracker.add_cube(new_pos)
    
    def decide_move_dir(self, action: KeyActions, front: Vector3):
        dir = Vector3([0.0, 0.0, 0.0])
        if abs(front.y) >= abs(front.x):
            dir.y = 1.0 if front.y>0 else -1.0
        else:
            dir.x = 1.0 if front.x>0 else -1.0
        return unit_size * self.cube_move_map[action](dir)
    
    def render_picker(self):
        self.vao_pick.render(gl.TRIANGLES, instances=self.cube_number)
        
    def render(self):
        self.vao.render(gl.TRIANGLES, instances=self.cube_number)
    
    @property
    def cube_number(self):
        return int(len(self.cubes) / 6)