import math
from pathlib import Path

import moderngl_window as mglw
import numpy as np

from blackhole import BlackHole
from camera import Camera
import glm
from lod import LODManager
from renderer import Renderer
from galaxy import GalacticBulge
from galactic_disk import GalacticDisk

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
        self.camera      = Camera()
        self.lod_manager = LODManager()
        self.bulge       = GalacticBulge(self.ctx, Path(__file__).parent)
        self.galactic_disk = GalacticDisk(self.ctx, Path(__file__).parent)
        
        self.galaxy_rotation_angle = 0.0



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
        # Medium Black Hole Shader
        # ==========================================================
        with open(BASE_DIR / "shaders" / "medium_blackhole_vert.glsl", encoding="utf-8") as f:
            medium_vert = f.read()
        with open(BASE_DIR / "shaders" / "medium_blackhole_frag.glsl", encoding="utf-8") as f:
            medium_frag = f.read()
        self.medium_program = self.ctx.program(
            vertex_shader=medium_vert,
            fragment_shader=medium_frag,
        )
        self.medium_vao = self.ctx.vertex_array(
            self.medium_program,
            [(self.main_quad_buffer, "2f", "in_position")]
        )

        # ==========================================================
        # Billboard Shader
        # ==========================================================
        with open(BASE_DIR / "shaders" / "billboard_vert.glsl", encoding="utf-8") as f:
            billboard_vert = f.read()
        with open(BASE_DIR / "shaders" / "billboard_frag.glsl", encoding="utf-8") as f:
            billboard_frag = f.read()
        self.billboard_program = self.ctx.program(
            vertex_shader=billboard_vert,
            fragment_shader=billboard_frag,
        )
        self.billboard_vao = self.ctx.vertex_array(
            self.billboard_program,
            [(self.main_quad_buffer, "2f", "in_position")]
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


        self.renderer = Renderer(
                    self.ctx,
                    self.program,
                    self.main_quad_vao,
                    self.medium_program,
                    self.medium_vao,
                    self.billboard_program,
                    self.billboard_vao
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
        self.depth_tex = self.ctx.depth_renderbuffer((width, height))

        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.scene_tex],
            depth_attachment=self.depth_tex
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
            self.camera.zoom_in(frametime)

        if self._zoom_out:
            self.camera.zoom_out(frametime)

        self.camera.update(frametime)
       

        # ----------------------------------------------------------
        # LOD
        # ----------------------------------------------------------

        lod_state = self.lod_manager.get_state(
            self.camera.distance
        )


        fps = 1.0 / max(frametime, 0.0001)
        
        self.galaxy_rotation_angle += frametime * 0.05
        
        print(
            f"Stars: {self.bulge.num_stars + self.galactic_disk.num_stars} "
            f"Bulge vis: {lod_state['bulge_visibility']:.2f} "
            f"Galaxy Rot: {self.galaxy_rotation_angle:.2f} "
            f"Dist: {self.camera.distance:.1f} "
            f"FPS: {fps:.1f}      ",
            end="\r",
            flush=True
        )
        
        # ----------------------------------------------------------
        # PASS 1
        # Render Scene
        # ----------------------------------------------------------

        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0, depth=1.0)
        
        # We need depth test for the stars, but disable depth mask so they don't occlude each other
        self.ctx.enable(self.ctx.DEPTH_TEST)
        self.ctx.depth_mask = False
        
        # Use standard additive blending for 3D stars
        self.ctx.blend_func = (self.ctx.SRC_ALPHA, self.ctx.ONE)

        # NEAR Shader Uniforms
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
            
        # Continuous LOD Parameters for NEAR
        if "u_lodDetail" in self.program:
            self.program["u_lodDetail"].value = lod_state["ray_march_detail"]
        if "u_volumetricDetail" in self.program:
            self.program["u_volumetricDetail"].value = lod_state["volumetric_detail"]
        if "u_diskThickness" in self.program:
            self.program["u_diskThickness"].value = lod_state["disk_thickness"]
        if "u_proceduralStarWeight" in self.program:
            self.program["u_proceduralStarWeight"].value = lod_state["near_weight"]

        # Medium LOD Uniforms
        if "u_camDistance" in self.medium_program:
            self.medium_program["u_camDistance"].value = self.camera.distance
        if "aspectRatio" in self.medium_program:
            self.medium_program["aspectRatio"].value = bh.aspect_ratio
        if "u_diskSquish" in self.medium_program:
            self.medium_program["u_diskSquish"].value = self.camera.disk_squish
        if "u_time" in self.medium_program:
            self.medium_program["u_time"].value = time
        if "u_azimuth" in self.medium_program:
            self.medium_program["u_azimuth"].value = self.camera.azimuth
        if "u_diskThickness" in self.medium_program:
            self.medium_program["u_diskThickness"].value = lod_state["disk_thickness"]
        if "u_glowIntensity" in self.medium_program:
            self.medium_program["u_glowIntensity"].value = lod_state["glow_intensity"]
        if "u_innerDisk" in self.medium_program:
            self.medium_program["u_innerDisk"].value = bh.inner_disk_radius
        if "u_outerDisk" in self.medium_program:
            self.medium_program["u_outerDisk"].value = bh.outer_disk_radius
        if "u_innerRingStrength" in self.medium_program:
            self.medium_program["u_innerRingStrength"].value = lod_state["inner_ring_strength"]
        if "u_dopplerStrength" in self.medium_program:
            self.medium_program["u_dopplerStrength"].value = lod_state["doppler_strength"]
        if "u_diskOuterRadius" in self.medium_program:
            self.medium_program["u_diskOuterRadius"].value = lod_state["disk_outer_radius"]
        if "u_volumetricDetail" in self.medium_program:
            self.medium_program["u_volumetricDetail"].value = lod_state["volumetric_detail"]
        if "u_proceduralStarWeight" in self.medium_program:
            self.medium_program["u_proceduralStarWeight"].value = lod_state["near_weight"]

        # Billboard LOD Uniforms
        if "u_camDistance" in self.billboard_program:
            self.billboard_program["u_camDistance"].value = self.camera.distance
        if "u_time" in self.billboard_program:
            self.billboard_program["u_time"].value = time
        if "aspectRatio" in self.billboard_program:
            self.billboard_program["aspectRatio"].value = bh.aspect_ratio
        if "u_diskSquish" in self.billboard_program:
            self.billboard_program["u_diskSquish"].value = self.camera.disk_squish
        if "u_azimuth" in self.billboard_program:
            self.billboard_program["u_azimuth"].value = self.camera.azimuth
        if "u_diskThickness" in self.billboard_program:
            self.billboard_program["u_diskThickness"].value = lod_state["disk_thickness"]
        if "u_glowIntensity" in self.billboard_program:
            self.billboard_program["u_glowIntensity"].value = lod_state["glow_intensity"]
        if "u_innerDisk" in self.billboard_program:
            self.billboard_program["u_innerDisk"].value = bh.inner_disk_radius
        if "u_outerDisk" in self.billboard_program:
            self.billboard_program["u_outerDisk"].value = bh.outer_disk_radius
        if "u_innerRingStrength" in self.billboard_program:
            self.billboard_program["u_innerRingStrength"].value = lod_state["inner_ring_strength"]
        if "u_dopplerStrength" in self.billboard_program:
            self.billboard_program["u_dopplerStrength"].value = lod_state["doppler_strength"]
        if "u_diskOuterRadius" in self.billboard_program:
            self.billboard_program["u_diskOuterRadius"].value = lod_state["disk_outer_radius"]
        if "u_volumetricDetail" in self.billboard_program:
            self.billboard_program["u_volumetricDetail"].value = lod_state["volumetric_detail"]
        if "u_proceduralStarWeight" in self.billboard_program:
            self.billboard_program["u_proceduralStarWeight"].value = lod_state["near_weight"]

        # Render Galactic Disk first, then Bulge
        # Fade out 3D stars when very close to avoid stacking over procedural stars
        base_visibility = 1.0 - lod_state["near_weight"]
        star_visibility = base_visibility
        
        # LOCAL 3-9 FIX ONLY: Restore 3D moving stars in the near region
        # Ensures they don't abruptly appear or disappear by blending from 2.0 to 9.0
        dist = self.camera.distance
        if 2.0 <= dist <= 9.0:
            def smoothstep_py(e0, e1, x):
                t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
                return t * t * (3.0 - 2.0 * t)
                
            # Get the exact base visibility that will be active at distance 9.0
            # to ensure a mathematically perfect, seamless merge.
            base_at_9 = 1.0 - self.lod_manager.get_state(9.0)["near_weight"]
            
            if dist < 4.0:
                # Ramp up: 0.0 at dist 2.0 -> ~0.125 at dist 3.0 -> 0.25 at dist 4.0
                t = smoothstep_py(2.0, 4.0, dist)
                local_vis = t * 0.25
            elif dist < 7.0:
                # Moderate to Strong: 0.25 at dist 4.0 -> ~0.30 at dist 5.0 -> 0.45 at dist 7.0
                t = smoothstep_py(4.0, 7.0, dist)
                local_vis = 0.25 * (1.0 - t) + 0.45 * t
            else:
                # Merge down to normal transition: 0.45 at dist 7.0 -> base_at_9 at dist 9.0
                t = smoothstep_py(7.0, 9.0, dist)
                local_vis = 0.45 * (1.0 - t) + base_at_9 * t
                
            star_visibility = local_vis
        
        self.galactic_disk.render(
            self.camera, 
            bh.aspect_ratio, 
            star_visibility, 
            self.galaxy_rotation_angle
        )
        self.bulge.render(
            self.camera, 
            bh.aspect_ratio, 
            star_visibility, 
            self.galaxy_rotation_angle
        )

        # ----------------------------------------------------------
        # Post-process passes (Black hole raymarcher)
        # ----------------------------------------------------------
        self.ctx.disable(self.ctx.DEPTH_TEST)
        self.ctx.depth_mask = True # restore depth mask
        
        # Composite mode: StarColor * Transmittance + GasColor * 1.0
        self.ctx.blend_func = (self.ctx.ONE, self.ctx.SRC_ALPHA)
        
        self.renderer.render(lod_state)
        # ----------------------------------------------------------
        # PASS 2
        # Post Processing
        # ----------------------------------------------------------

        self.ctx.screen.use()

        self.ctx.clear(0.02, 0.02, 0.03, 1.0)
        self.ctx.disable(self.ctx.DEPTH_TEST)

        self.scene_tex.use(location=0)

        self.post_program["scene"].value = 0

        self.quad_vao.render(mode=self.ctx.TRIANGLE_STRIP)


if __name__ == "__main__":
    mglw.run_window_config(MilkyWaySimulation)