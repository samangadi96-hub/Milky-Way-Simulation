import math
from pathlib import Path

import moderngl_window as mglw
import numpy as np

from blackhole import BlackHole
from camera import Camera


class MilkyWaySimulation(mglw.WindowConfig):

    gl_version = (3, 3)
    title = "Milky Way Simulation"

    window_size = (1280, 720)
    resizable = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("Window created")
        print(type(self.wnd))
        # ==========================================================
        # Scene Objects
        # ==========================================================

        self.blackhole = BlackHole()
        self.camera = Camera()
        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False

        BASE_DIR = Path(__file__).parent

        # ==========================================================
        # Load Main Shaders
        # ==========================================================

        with open(BASE_DIR / "shaders" / "vertex.glsl", encoding="utf-8") as f:
            vertex_shader = f.read()

        with open(BASE_DIR / "shaders" / "fragment.glsl", encoding="utf-8") as f:
            fragment_shader = f.read()

        self.program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader,
        )

        # ==========================================================
        # Fullscreen Quad
        # ==========================================================

        quad = np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0,
        ], dtype="f4")

        self.main_quad_buffer = self.ctx.buffer(quad)

        self.main_quad_vao = self.ctx.vertex_array(
            self.program,
            [
                (self.main_quad_buffer, "2f", "in_position")
            ],
        )

        # ==========================================================
        # Create Framebuffer
        # ==========================================================

        self.create_framebuffer(*self.wnd.size)

        # ==========================================================
        # Load Post Processing Shaders
        # ==========================================================

        with open(BASE_DIR / "shaders" / "post_vert.glsl", encoding="utf-8") as f:
            post_vert = f.read()

        with open(BASE_DIR / "shaders" / "post_frag.glsl", encoding="utf-8") as f:
            post_frag = f.read()

        self.post_program = self.ctx.program(
            vertex_shader=post_vert,
            fragment_shader=post_frag,
        )

        quad2 = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype="f4")

        self.quad_buffer = self.ctx.buffer(quad2)

        self.quad_vao = self.ctx.vertex_array(
            self.post_program,
            [
                (self.quad_buffer, "2f 2f", "in_vert", "in_texcoord")
            ],
        )

        # ==========================================================
        # Rendering Settings
        # ==========================================================

        self.ctx.enable(self.ctx.BLEND)

        self.ctx.blend_func = (
            self.ctx.SRC_ALPHA,
            self.ctx.ONE_MINUS_SRC_ALPHA,
        )

    # ==============================================================
    # Framebuffer
    # ==============================================================

    def create_framebuffer(self, width, height):

        self.scene_tex = self.ctx.texture((width, height), 4)

        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.scene_tex]
        )

    # ==============================================================
    # Window Resize
    # ==============================================================

    def resize(self, width: int, height: int):

        self.scene_tex.release()
        self.fbo.release()

        self.create_framebuffer(width, height)

        self.blackhole.aspect_ratio = width / height

    # ==============================================================
    # Keyboard Controls
    # ==============================================================
    
    def key_event(self, key, action, modifiers):

        if action == self.wnd.keys.ACTION_PRESS:

            if key in (self.wnd.keys.W, self.wnd.keys.UP):
                self.move_up = True

            elif key in (self.wnd.keys.S, self.wnd.keys.DOWN):
                self.move_down = True

            elif key in (self.wnd.keys.A, self.wnd.keys.LEFT):
                self.move_left = True

            elif key in (self.wnd.keys.D, self.wnd.keys.RIGHT):
                self.move_right = True

        elif action == self.wnd.keys.ACTION_RELEASE:

            if key in (self.wnd.keys.W, self.wnd.keys.UP):
                self.move_up = False

            elif key in (self.wnd.keys.S, self.wnd.keys.DOWN):
                self.move_down = False

            elif key in (self.wnd.keys.A, self.wnd.keys.LEFT):
                self.move_left = False

            elif key in (self.wnd.keys.D, self.wnd.keys.RIGHT):
                self.move_right = False
   # ==============================================================
    # Render Loop
    # ==============================================================

    def on_render(self, time, frametime):

        keys = self.wnd.keys
        bh = self.blackhole

        if self.wnd.is_key_pressed(keys.W):
            print("W is held")
            self.camera.look_up()

        if self.wnd.is_key_pressed(keys.S):
            print("S is held")
            self.camera.look_down()
        
        if self.wnd.is_key_pressed(keys.A):
            print("A is held")
            self.camera.rotate_left(frametime)

        if self.wnd.is_key_pressed(keys.D):
            print("D is held")
            self.camera.rotate_right(frametime)

        self.camera.update(frametime)

        print(
            f"Azimuth = {math.degrees(self.camera.azimuth):.2f}",
            end="\r"
        )
        
        # ----------------------------------------------------------
        # PASS 1 (Keep the rest of your render code exactly the same below here)
        # PASS 1
        # Render Scene
        # ----------------------------------------------------------

        self.fbo.use()

        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        # Send all physical parameters as uniforms ONLY if the shader is actively using them
        if "u_time" in self.program:
            self.program["u_time"].value = time
            
        if "aspectRatio" in self.program:
            self.program["aspectRatio"].value = bh.aspect_ratio
            
        if "u_eventHorizon" in self.program:
            self.program["u_eventHorizon"].value = bh.event_horizon_radius
            
        if "u_photonSphere" in self.program:
            self.program["u_photonSphere"].value = bh.photon_sphere_radius
            
        if "u_innerDisk" in self.program:
            self.program["u_innerDisk"].value = bh.inner_disk_radius
            
        if "u_outerDisk" in self.program:
            self.program["u_outerDisk"].value = bh.outer_disk_radius
            
        if "u_diskSquish" in self.program:
            self.program["u_diskSquish"].value = self.camera.disk_squish

        if "u_azimuth" in self.program:
            self.program["u_azimuth"].value = self.camera.azimuth

        self.main_quad_vao.render(mode=self.ctx.TRIANGLE_STRIP)

        # ----------------------------------------------------------
        # PASS 2
        # Post Processing
        # ----------------------------------------------------------

        self.ctx.screen.use()

        self.ctx.clear(0.02, 0.02, 0.03, 1.0)

        self.scene_tex.use(location=0)

        self.post_program["scene"].value = 0

        self.quad_vao.render(mode=self.ctx.TRIANGLE_STRIP)


if __name__ == "__main__":
    mglw.run_window_config(MilkyWaySimulation)