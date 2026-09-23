import numpy as np
import moderngl
import glm

class GalacticBulge:
    def __init__(self, ctx, base_dir):
        self.ctx = ctx
        self.num_stars = 800000
        
        # Load shaders
        with open(base_dir / "shaders" / "bulge_vert.glsl", encoding="utf-8") as f:
            vert_code = f.read()
        with open(base_dir / "shaders" / "bulge_frag.glsl", encoding="utf-8") as f:
            frag_code = f.read()
            
        self.program = self.ctx.program(
            vertex_shader=vert_code,
            fragment_shader=frag_code,
        )
        
        # Generate stars
        # Use an ellipsoidal Gaussian/exponential distribution
        # We can use normal distribution for x, y, z
        x = np.random.normal(0, 2.5, self.num_stars)
        z = np.random.normal(0, 2.5, self.num_stars)
        y = np.random.normal(0, 0.6, self.num_stars) # Compressed vertically
        
        # Add a dense central core
        core_stars = int(self.num_stars * 0.5)
        r_core = np.random.exponential(1.0, core_stars)
        theta = np.random.uniform(0, 2*np.pi, core_stars)
        phi = np.arccos(np.random.uniform(-1, 1, core_stars))
        
        x[:core_stars] = r_core * np.sin(phi) * np.cos(theta)
        z[:core_stars] = r_core * np.sin(phi) * np.sin(theta)
        y[:core_stars] = r_core * np.cos(phi) * 0.4
        
        # Create a small hollow center so stars don't overlap the exact singularity center (optional)
        # But the prompt says the black hole is at 0,0,0 and bulge around it.
        
        positions = np.column_stack((x, y, z)).astype('f4')
        
        # Colors: Older/cooler bulge stars
        colors = np.zeros((self.num_stars, 3), dtype='f4')
        rand_c = np.random.random(self.num_stars)
        
        cool = rand_c < 0.45
        med = (rand_c >= 0.45) & (rand_c < 0.85)
        hot = rand_c >= 0.85
        
        # Cool: Red/Orange
        colors[cool] = [1.0, 0.3, 0.1] + np.random.normal(0, 0.05, (cool.sum(), 3))
        # Med: Yellow/Orange
        colors[med] = [1.0, 0.7, 0.3] + np.random.normal(0, 0.05, (med.sum(), 3))
        # Hot: Warm white
        colors[hot] = [1.0, 0.95, 0.8] + np.random.normal(0, 0.05, (hot.sum(), 3))
        colors = np.clip(colors, 0.0, 1.0)
        
        # Sizes: 90% tiny, 8% medium, 2% bright
        sizes = np.zeros(self.num_stars, dtype='f4')
        rand_s = np.random.random(self.num_stars)
        tiny = rand_s < 0.9
        med_s = (rand_s >= 0.9) & (rand_s < 0.98)
        large = rand_s >= 0.98
        
        sizes[tiny] = np.random.uniform(0.01, 0.04, tiny.sum())
        sizes[med_s] = np.random.uniform(0.05, 0.1, med_s.sum())
        sizes[large] = np.random.uniform(0.12, 0.25, large.sum())
        
        # Brightness
        brightness = np.random.uniform(0.4, 0.8, self.num_stars).astype('f4')
        brightness[large] = np.random.uniform(1.0, 2.0, large.sum())
        
        star_data = np.column_stack((positions, colors, sizes, brightness)).astype('f4')
        
        self.vbo = self.ctx.buffer(star_data.tobytes())
        self.vao = self.ctx.vertex_array(
            self.program,
            [(self.vbo, '3f 3f 1f 1f', 'in_position', 'in_color', 'in_size', 'in_brightness')]
        )
        
    def render(self, camera, aspect_ratio, visibility, rotation_angle):
        if visibility <= 0.001:
            return
            
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE
        # Disable depth write so stars don't occlude each other in weird ways, 
        # but MilkyWay simulation probably runs without depth test anyway.
        
        if "u_visibility" in self.program:
            self.program["u_visibility"].value = visibility
            
        if "u_view" in self.program:
            self.program["u_view"].write(camera.get_view_matrix())
        if "u_projection" in self.program:
            self.program["u_projection"].write(camera.get_projection_matrix(aspect_ratio))
        if "u_model" in self.program:
            model = glm.rotate(glm.mat4(1.0), rotation_angle, glm.vec3(0.0, 1.0, 0.0))
            self.program["u_model"].write(model)
            
        self.vao.render(moderngl.POINTS)
