import numpy as np
import moderngl
import glm

class GalacticDisk:
    def __init__(self, ctx, base_dir):
        self.ctx = ctx
        self.num_stars = 200000
        
        # Load shaders (reusing bulge shaders for now, but they will have u_galaxyAngle)
        with open(base_dir / "shaders" / "bulge_vert.glsl", encoding="utf-8") as f:
            vert_code = f.read()
        with open(base_dir / "shaders" / "bulge_frag.glsl", encoding="utf-8") as f:
            frag_code = f.read()
            
        self.program = self.ctx.program(
            vertex_shader=vert_code,
            fragment_shader=frag_code,
        )
        
        # ==========================================================
        # Spiral Galaxy Parameters
        # ==========================================================
        ARM_COUNT = 4
        SPIRAL_TIGHTNESS = 2.5      # 'b' in theta = b * log(r/r0)
        ARM_WIDTH = 0.35       # Base angular width
        ARM_STRENGTH = 0.85     # Max proportion of stars in arms
        INNER_RADIUS = 2.0
        OUTER_RADIUS = 45.0
        BULGE_RADIUS = 6.0          # Where arms fully emerge
        
        # 1. Generate Radii
        # Base exponential distribution to keep the overall disk density profile
        radius = np.random.exponential(8.0, self.num_stars)
        radius = np.clip(radius, INNER_RADIUS, OUTER_RADIUS)
        
        # 2. Determine Arm vs Inter-arm Population (Density Waves)
        # Arms emerge smoothly from the bulge
        def smoothstep(edge0, edge1, x):
            t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
            return t * t * (3.0 - 2.0 * t)
            
        arm_strength = smoothstep(INNER_RADIUS, BULGE_RADIUS, radius)
        
        # Probability of a star belonging to an arm
        p_arm = ARM_STRENGTH * arm_strength
        is_arm = np.random.random(self.num_stars) < p_arm
        
        # 3. Calculate Angles
        theta = np.zeros(self.num_stars)
        
        # Inter-arm stars: uniformly distributed in angle
        theta[~is_arm] = np.random.uniform(0, 2 * np.pi, np.sum(~is_arm))
        
        # Arm stars: distributed along logarithmic spirals
        num_arm_stars = np.sum(is_arm)
        
        # Slightly vary density between arms to make it less perfect
        arm_probs = np.array([0.27, 0.23, 0.26, 0.24])
        arm_indices = np.random.choice(ARM_COUNT, p=arm_probs, size=num_arm_stars)
        arm_base_angles = arm_indices * (2 * np.pi / ARM_COUNT)
        
        # Base logarithmic spiral angle: theta = theta0 + b * log(r / r0)
        ideal_theta = arm_base_angles + SPIRAL_TIGHTNESS * np.log(radius[is_arm] / INNER_RADIUS)
        
        # Slightly vary width between arms
        arm_widths = np.array([1.0, 1.1, 0.9, 1.05]) * ARM_WIDTH
        
        # Angular spread: tighter near the core, slightly wider at the edges (optional, but realistic)
        # Using a Gaussian falloff around the arm center
        spread = np.random.normal(0, arm_widths[arm_indices], num_arm_stars)
        
        theta[is_arm] = ideal_theta + spread
        
        # 4. 3D Structure
        x = radius * np.cos(theta)
        z = radius * np.sin(theta)
        
        # Thickness: very thin compared to radius, slightly thicker in the middle
        thickness_scale = 0.2 + 0.3 * np.exp(-radius / 10.0)
        y = np.random.normal(0, 1.0, self.num_stars) * thickness_scale
        
        positions = np.column_stack((x, y, z)).astype('f4')
        
        # 5. Star Colors
        colors = np.zeros((self.num_stars, 3), dtype='f4')
        rand_c = np.random.random(self.num_stars)
        
        # Inter-arm / older population: yellow, orange, warm white
        inter_arm_mask = ~is_arm
        n_inter = np.sum(inter_arm_mask)
        inter_c = np.zeros((n_inter, 3))
        r_inter = rand_c[inter_arm_mask]
        
        inter_c[r_inter < 0.4] = [1.0, 0.7, 0.3] # Yellow-orange
        inter_c[(r_inter >= 0.4) & (r_inter < 0.8)] = [1.0, 0.5, 0.1] # Orange
        inter_c[r_inter >= 0.8] = [1.0, 0.95, 0.8] # Warm white
        colors[inter_arm_mask] = inter_c
        
        # Arm population: more white, some blue/white stars (blue stars are a minority)
        arm_mask = is_arm
        n_arm = np.sum(arm_mask)
        arm_c = np.zeros((n_arm, 3))
        r_arm = rand_c[arm_mask]
        
        arm_c[r_arm < 0.4] = [1.0, 1.0, 1.0] # Pure white
        arm_c[(r_arm >= 0.4) & (r_arm < 0.7)] = [0.9, 0.95, 1.0] # Blue-white
        arm_c[(r_arm >= 0.7) & (r_arm < 0.9)] = [1.0, 0.95, 0.8] # Warm white
        arm_c[r_arm >= 0.9] = [1.0, 0.8, 0.5] # Occasional yellow/orange
        colors[arm_mask] = arm_c
        
        # Add slight color variance
        colors += np.random.normal(0, 0.05, (self.num_stars, 3))
        colors = np.clip(colors, 0.0, 1.0)
        
        # 6. Star Sizes: 90% tiny, 8% medium, 2% bright
        sizes = np.zeros(self.num_stars, dtype='f4')
        rand_s = np.random.random(self.num_stars)
        tiny = rand_s < 0.9
        med_s = (rand_s >= 0.9) & (rand_s < 0.98)
        large = rand_s >= 0.98
        
        sizes[tiny] = np.random.uniform(0.01, 0.03, tiny.sum())
        sizes[med_s] = np.random.uniform(0.04, 0.07, med_s.sum())
        sizes[large] = np.random.uniform(0.1, 0.2, large.sum())
        
        # Brightness
        brightness = np.random.uniform(0.3, 0.7, self.num_stars).astype('f4')
        brightness[large] = np.random.uniform(0.8, 1.5, large.sum())
        
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
