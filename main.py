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


    def on_render(self, time, frametime):

        # Background
        self.ctx.clear(0.15, 0.15, 0.18)

        # Draw Photon Ring
        
        self.program["objectColor"].value = (1.0, 0.65, 0.15)

        self.photon_vao.render(mode=self.ctx.TRIANGLE_STRIP)

        # Draw Event Horizon
      
        self.program["objectColor"].value = (0.0, 0.0, 0.0)

        self.event_vao.render(mode=self.ctx.TRIANGLE_FAN)


if __name__ == "__main__":
    mglw.run_window_config(MilkyWaySimulation)