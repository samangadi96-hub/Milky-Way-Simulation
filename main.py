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
        print(type(self.wnd))
        # ==========================================================
        # Scene Objects
        # ==========================================================

        self.blackhole = BlackHole()
        self.camera = Camera()

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

        if action not in (
            self.wnd.keys.ACTION_PRESS,
            self.wnd.keys.ACTION_REPEAT,
        ):
            return

        if key in (
            self.wnd.keys.W,
            self.wnd.keys.UP,
        ):
            self.camera.look_up()

        elif key in (
            self.wnd.keys.S,
            self.wnd.keys.DOWN,
        ):
            self.camera.look_down()

    # ==============================================================
    # Render Loop
    # ==============================================================

    def on_render(self, time, frametime):

        bh = self.blackhole

        # Update Camera
        self.camera.update(frametime)
        
        print(
            f"Current: {math.degrees(self.camera.inclination):.2f}",
            end="\r"
        )
        # ----------------------------------------------------------
        # PASS 1
        # Render Scene
        # ----------------------------------------------------------

        self.fbo.use()

        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        self.program["u_time"].value = time
        self.program["aspectRatio"].value = bh.aspect_ratio

        self.program["u_eventHorizon"].value = bh.event_horizon_radius
        self.program["u_photonSphere"].value = bh.photon_sphere_radius

        self.program["u_innerDisk"].value = bh.inner_disk_radius
        self.program["u_outerDisk"].value = bh.outer_disk_radius

        self.program["u_diskSquish"].value = self.camera.disk_squish

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