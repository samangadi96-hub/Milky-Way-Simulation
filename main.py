import math
from pathlib import Path

import moderngl_window as mglw
import numpy as np

from blackhole import BlackHole
from camera import Camera
from lod import LODManager
from renderer import Renderer
from scene import Galaxy

class MilkyWaySimulation(mglw.WindowConfig):

    gl_version = (3, 3)
    title = "Milky Way Simulation"

    window_size = (1280, 720)
    resizable = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ==========================================================
        # Scene Objects
        # ==========================================================

        self.blackhole   = BlackHole()
        self.galaxy      = Galaxy()
        self.camera      = Camera()
        self.lod_manager = LODManager()

        # Keyboard state flags
        self.move_up    = False
        self.move_down  = False
        self.move_left  = False
        self.move_right = False
        self._zoom_in   = False
        self._zoom_out  = False

        print()
        print('  Milky Way Simulation - Controls')
        print('  --------------------------------')
        print('  Mouse Left-drag  -> orbit galaxy')
        print('  Mouse Scroll     -> zoom in / out')
        print('  W/S / Up/Down    -> tilt camera')
        print('  A/D / Left/Right -> rotate camera')
        print('  Q / E            -> zoom in / out')
        print('  --------------------------------')
        print()

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
        # Galaxy Shader
        # ==========================================================

        with open(
            BASE_DIR / "shaders" / "galaxy_vertex.glsl",
            encoding="utf-8"
        ) as f:
            galaxy_vertex_shader = f.read()

        with open(
            BASE_DIR / "shaders" / "galaxy_fragment.glsl",
            encoding="utf-8"
        ) as f:
            galaxy_fragment_shader = f.read()

        self.galaxy_program = self.ctx.program(
    vertex_shader=galaxy_vertex_shader,
    fragment_shader=galaxy_fragment_shader,
)

        self.galaxy_vao = self.ctx.vertex_array(
            self.galaxy_program,
            [
                (self.main_quad_buffer, "2f", "in_position")
            ],
    )

        self.renderer = Renderer(
                    self.ctx,
                    self.program,
                    self.main_quad_vao,
                    self.galaxy_program,
                    self.galaxy_vao
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

    def on_resize(self, width: int, height: int):

        self.scene_tex.release()
        self.fbo.release()

        self.create_framebuffer(width, height)

        self.blackhole.aspect_ratio = width / height

    # ==============================================================
    # Mouse Controls
    # ==============================================================

    def on_mouse_press_event(self, x: int, y: int, button: int):
        self.camera.on_mouse_press(x, y, button)

    def on_mouse_release_event(self, x: int, y: int, button: int):
        self.camera.on_mouse_release(x, y, button)

    def on_mouse_drag_event(self, x: int, y: int, dx: int, dy: int):
        self.camera.on_mouse_drag(x, y, dx, dy, buttons=1)

    def on_mouse_scroll_event(self, x_offset: float, y_offset: float):
        self.camera.on_mouse_scroll(0, 0, x_offset, y_offset)

    # ==============================================================
    # Keyboard Controls
    # ==============================================================

    def on_key_event(self, key, action, modifiers):

        if action == self.wnd.keys.ACTION_PRESS:

            if key in (self.wnd.keys.W, self.wnd.keys.UP):
                self.move_up = True

            elif key in (self.wnd.keys.S, self.wnd.keys.DOWN):
                self.move_down = True

            elif key in (self.wnd.keys.A, self.wnd.keys.LEFT):
                self.move_left = True

            elif key in (self.wnd.keys.D, self.wnd.keys.RIGHT):
                self.move_right = True

            elif key == self.wnd.keys.Q:
                self._zoom_in = True

            elif key == self.wnd.keys.E:
                self._zoom_out = True

        elif action == self.wnd.keys.ACTION_RELEASE:

            if key in (self.wnd.keys.W, self.wnd.keys.UP):
                self.move_up = False

            elif key in (self.wnd.keys.S, self.wnd.keys.DOWN):
                self.move_down = False

            elif key in (self.wnd.keys.A, self.wnd.keys.LEFT):
                self.move_left = False

            elif key in (self.wnd.keys.D, self.wnd.keys.RIGHT):
                self.move_right = False

            elif key == self.wnd.keys.Q:
                self._zoom_in = False

            elif key == self.wnd.keys.E:
                self._zoom_out = False
   # ==============================================================
    # Render Loop
    # ==============================================================

    def on_render(self, time, frametime):

        bh = self.blackhole

        if self.move_up:
            self.camera.look_up()

        if self.move_down:
            self.camera.look_down()

        if self.move_left:
            self.camera.rotate_left(frametime)

        if self.move_right:
            self.camera.rotate_right(frametime)

        if self._zoom_in:
            self.camera.zoom_in()

        if self._zoom_out:
            self.camera.zoom_out()

        self.camera.update(frametime)

        # ----------------------------------------------------------
        # LOD
        # ----------------------------------------------------------

        lod_level = self.lod_manager.get_level(
        self.camera.distance
    )

        # ----------------------------------------------------------
        # Galaxy shader uniforms
        # ----------------------------------------------------------

        if "u_inclination" in self.galaxy_program:
            self.galaxy_program["u_inclination"].value = (
                self.camera.inclination
            )

        if "u_azimuth" in self.galaxy_program:
            self.galaxy_program["u_azimuth"].value = (
                self.camera.azimuth
            )

        if "u_galaxyRadius" in self.galaxy_program:
            self.galaxy_program["u_galaxyRadius"].value = (
                self.galaxy.radius
            )

        if "u_bulgeRadius" in self.galaxy_program:
            self.galaxy_program["u_bulgeRadius"].value = (
                self.galaxy.bulge_radius
            )

        if "u_armTightness" in self.galaxy_program:
            self.galaxy_program["u_armTightness"].value = (
                self.galaxy.arm_tightness
            )

        if "u_numArms" in self.galaxy_program:
            self.galaxy_program["u_numArms"].value = (
                self.galaxy.num_arms
            )
        lod_name = self.lod_manager.get_level_name(
            lod_level
        )


        print(
            f"Distance = {self.camera.distance:.2f} | "
            f"LOD = {lod_name:<6}",
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

        if "u_camDistance" in self.program:
            self.program["u_camDistance"].value = self.camera.distance

        self.renderer.render(lod_level)
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