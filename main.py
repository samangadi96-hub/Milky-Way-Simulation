import moderngl_window as mglw
from pathlib import Path
import numpy as np
import math

from blackhole import BlackHole


class MilkyWaySimulation(mglw.WindowConfig):

    gl_version = (3, 3)
    title = "Milky Way Simulation"
    window_size = (1280, 720)
    resizable = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.blackhole = BlackHole()

        BASE_DIR = Path(__file__).parent

        with open(BASE_DIR / "shaders" / "vertex.glsl", encoding="utf-8") as f:
            vertex_shader = f.read()

        with open(BASE_DIR / "shaders" / "fragment.glsl", encoding="utf-8") as f:
            fragment_shader = f.read()

        self.program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader,
        )

        # ============================================================
        # FULLSCREEN QUAD
        # ============================================================

        quad_data = np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0,
        ], dtype='f4')

        self.main_quad_buffer = self.ctx.buffer(quad_data)

        self.main_quad_vao = self.ctx.vertex_array(
            self.program,
            [(self.main_quad_buffer, '2f', 'in_position')]
        )

        # ============================================================
        # POST PROCESSING
        # ============================================================

        width, height = self.wnd.size

        self.scene_tex = self.ctx.texture((width, height), 4)

        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.scene_tex]
        )

        with open(BASE_DIR / "shaders" / "post_vert.glsl", encoding="utf-8") as f:
            post_vert = f.read()

        with open(BASE_DIR / "shaders" / "post_frag.glsl", encoding="utf-8") as f:
            post_frag = f.read()

        self.post_program = self.ctx.program(
            vertex_shader=post_vert,
            fragment_shader=post_frag
        )

        post_quad_data = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype='f4')

        self.quad_buffer = self.ctx.buffer(post_quad_data)

        self.quad_vao = self.ctx.vertex_array(
            self.post_program,
            [(self.quad_buffer, '2f 2f', 'in_vert', 'in_texcoord')]
        )

        # Alpha blending
        self.ctx.enable(self.ctx.BLEND)

        self.ctx.blend_func = (
            self.ctx.SRC_ALPHA,
            self.ctx.ONE_MINUS_SRC_ALPHA
        )

    # ============================================================
    # Keyboard Controls
    #
    # W / Up    -> Face-on
    # S / Down  -> Edge-on
    # ============================================================

    def key_event(self, key, action, modifiers):

        if action not in (
            self.wnd.keys.ACTION_PRESS,
            self.wnd.keys.ACTION_REPEAT,
        ):
            return

        step = math.radians(2)

        if key in (
            self.wnd.keys.W,
            self.wnd.keys.UP,
        ):
            self.blackhole.target_inclination -= step

        elif key in (
            self.wnd.keys.S,
            self.wnd.keys.DOWN,
        ):
            self.blackhole.target_inclination += step

        self.blackhole.target_inclination = max(
            0.0,
            min(
                math.radians(89.0),
                self.blackhole.target_inclination,
            ),
        )

        print(
            f"Inclination : "
            f"{math.degrees(self.blackhole.target_inclination):.1f}°"
        )

    # ============================================================
    # Render
    # ============================================================

    def on_render(self, time, frametime):

        bh = self.blackhole

        # Smoothly update inclination
        bh.update(frametime)

        # ==========================================
        # PASS 1
        # ==========================================

        self.fbo.use()

        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

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
            self.program["u_diskSquish"].value = bh.disk_squish

        self.main_quad_vao.render(mode=self.ctx.TRIANGLE_STRIP)

        # ==========================================
        # PASS 2
        # ==========================================

        self.ctx.screen.use()

        self.ctx.clear(0.02, 0.02, 0.03, 1.0)

        self.scene_tex.use(location=0)

        self.post_program["scene"].value = 0

        self.quad_vao.render(mode=self.ctx.TRIANGLE_STRIP)


if __name__ == "__main__":
    mglw.run_window_config(MilkyWaySimulation)