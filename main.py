import moderngl_window as mglw
from pathlib import Path

from blackhole import BlackHole


class MilkyWaySimulation(mglw.WindowConfig):

    gl_version = (3, 3)
    title = "Milky Way Simulation"

    window_size = (1280, 720)
    resizable = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create Black Hole
       
        self.blackhole = BlackHole()

        # Load Shaders
       
        BASE_DIR = Path(__file__).parent

        with open(BASE_DIR / "shaders" / "vertex.glsl") as f:
            vertex_shader = f.read()

        with open(BASE_DIR / "shaders" / "fragment.glsl") as f:
            fragment_shader = f.read()

        self.program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader,
        )

        # EVENT HORIZON
      

        event_vertices = self.blackhole.generate_event_horizon()

        self.event_vbo = self.ctx.buffer(event_vertices.tobytes())

        self.event_vao = self.ctx.vertex_array(
            self.program,
            [
                (self.event_vbo, "2f", "in_position")
            ]
        )

        # PHOTON RING
      

        photon_vertices = self.blackhole.generate_photon_ring()

        self.photon_vbo = self.ctx.buffer(photon_vertices.tobytes())

        self.photon_vao = self.ctx.vertex_array(
            self.program,
            [
                (self.photon_vbo, "2f", "in_position")
            ]
        )

        # ACCRETION DISK

        disk_vertices = self.blackhole.generate_accretion_disk()

        self.disk_vbo = self.ctx.buffer(disk_vertices.tobytes())

        self.disk_vao = self.ctx.vertex_array(
            self.program,
            [
                (self.disk_vbo, "2f", "in_position")
            ]
        )

        # Enable alpha blending for the gradient ring
        self.ctx.enable(self.ctx.BLEND)
        self.ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA


    def on_render(self, time, frametime):

        # Background
        self.ctx.clear(0.15, 0.15, 0.18)

        # Draw Accretion Disk (Stage 4) — behind everything
        self.program["useGradient"].value = 2
        self.program["innerRadius"].value = self.blackhole.inner_disk_radius
        self.program["outerRadius"].value = self.blackhole.outer_disk_radius
        self.program["aspectRatio"].value = self.blackhole.aspect_ratio

        self.disk_vao.render(mode=self.ctx.TRIANGLE_STRIP)

        # Draw Photon Ring (Stage 3: gradient yellow -> orange -> transparent)
        self.program["useGradient"].value = 1
        self.program["innerRadius"].value = self.blackhole.event_horizon_radius
        self.program["outerRadius"].value = self.blackhole.photon_sphere_radius
        self.program["aspectRatio"].value = self.blackhole.aspect_ratio

        self.photon_vao.render(mode=self.ctx.TRIANGLE_STRIP)

        # Draw Event Horizon (solid black, no gradient)
        self.program["useGradient"].value = 0
        self.program["objectColor"].value = (0.0, 0.0, 0.0)

        self.event_vao.render(mode=self.ctx.TRIANGLE_FAN)


if __name__ == "__main__":
    mglw.run_window_config(MilkyWaySimulation)