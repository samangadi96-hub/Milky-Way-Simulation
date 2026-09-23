import numpy as np

class NebulaManager:
    def __init__(self, num_nebulae=100):
        # Deterministic generation
        np.random.seed(1337)
        
        self.num_nebulae = num_nebulae
        self.nebulae_data = [] # List of dicts for shader uniforms
        self.stars_data = []   # List of stars to add to galactic disk
        
        # Spiral Parameters (must match galactic_disk.py)
        ARM_COUNT = 4
        SPIRAL_TIGHTNESS = 2.5
        INNER_RADIUS = 2.0
        
        # We want nebulae mostly in the active star-forming ring
        MIN_R = 6.0
        MAX_R = 40.0
        
        # Emission colors
        # Deep red/pink for H-II regions
        color_hii_1 = np.array([1.0, 0.15, 0.3])
        color_hii_2 = np.array([1.0, 0.25, 0.4])
        color_hii_3 = np.array([0.9, 0.05, 0.2])
        
        # Blue/white for reflection
        color_ref_1 = np.array([0.4, 0.6, 1.0])
        color_ref_2 = np.array([0.3, 0.5, 0.9])
        
        for i in range(num_nebulae):
            # 1. Position along spiral arms
            # Preferentially place in the denser parts (r ~ 10-35)
            r = np.random.gamma(shape=4.0, scale=4.0) + MIN_R
            r = np.clip(r, MIN_R, MAX_R)
            
            # Select arm
            arm_index = np.random.randint(0, ARM_COUNT)
            arm_base_angle = arm_index * (2 * np.pi / ARM_COUNT)
            
            # Ideal log spiral angle
            ideal_theta = arm_base_angle + SPIRAL_TIGHTNESS * np.log(r / INNER_RADIUS)
            
            # Slight offset inside/outside the arm
            theta_offset = np.random.normal(0, 0.15)
            theta = ideal_theta + theta_offset
            
            # 3D Position
            x = r * np.cos(theta)
            z = r * np.sin(theta)
            
            # Nebulae are very close to the galactic plane (thin disk)
            y = np.random.normal(0, 0.1)
            
            # 2. Size and Type
            size_roll = np.random.random()
            if size_roll < 0.1: # 10% hero regions
                radius = np.random.uniform(3.0, 5.0)
                density = np.random.uniform(1.0, 1.5)
            elif size_roll < 0.3: # 20% medium regions
                radius = np.random.uniform(1.5, 3.0)
                density = np.random.uniform(0.7, 1.1)
            else: # 70% small faint regions
                radius = np.random.uniform(0.6, 1.5)
                density = np.random.uniform(0.4, 0.7)
                
            # Reflection fraction (minority are blue)
            ref_roll = np.random.random()
            if ref_roll < 0.05: # 5% strong reflection
                c = color_ref_1
                emission_strength = np.random.uniform(1.2, 2.0)
            elif ref_roll < 0.2: # 15% weak reflection / mixed
                c = color_ref_2 * 0.5 + color_hii_1 * 0.5
                emission_strength = np.random.uniform(1.0, 1.5)
            else: # 80% H-II
                c_roll = np.random.random()
                if c_roll < 0.33: c = color_hii_1
                elif c_roll < 0.66: c = color_hii_2
                else: c = color_hii_3
                emission_strength = np.random.uniform(1.5, 2.5)
                
            # Add some variance to color
            c = c + np.random.normal(0, 0.05, 3)
            c = np.clip(c, 0.0, 1.0)
            
            # Pack metadata into the shader
            # w of position = radius
            # w of color = combined density/emission parameter
            self.nebulae_data.append({
                'position': [x, y, z, radius],
                'color': [c[0], c[1], c[2], density * emission_strength]
            })
            
            # 3. Generate Young Bright Stars associated with this nebula
            if size_roll < 0.3: # Only medium and hero regions have noticeable bright young stars
                num_stars = np.random.randint(2, 6) if size_roll < 0.1 else np.random.randint(1, 3)
                for _ in range(num_stars):
                    # Place star inside/near the nebula
                    sx = x + np.random.normal(0, radius * 0.3)
                    sy = y + np.random.normal(0, radius * 0.1)
                    sz = z + np.random.normal(0, radius * 0.3)
                    
                    # Hot blue-white colors
                    sc_roll = np.random.random()
                    if sc_roll < 0.5:
                        scolor = [0.9, 0.95, 1.0]
                    else:
                        scolor = [0.8, 0.9, 1.0]
                        
                    # Large sizes and high brightness
                    ssize = np.random.uniform(0.1, 0.2)
                    sbright = np.random.uniform(1.5, 2.5)
                    
                    self.stars_data.append([sx, sy, sz, scolor[0], scolor[1], scolor[2], ssize, sbright])

    def get_stars_array(self):
        if not self.stars_data:
            return np.zeros((0, 8), dtype='f4')
        return np.array(self.stars_data, dtype='f4')

    def get_shader_uniforms(self):
        """Returns two flat lists of floats for the shader arrays."""
        positions = []
        colors = []
        for n in self.nebulae_data:
            positions.extend(n['position'])
            colors.extend(n['color'])
            
        # Pad up to a maximum number (e.g. 150) if needed
        MAX_NEBULAE = 150
        while len(positions) // 4 < MAX_NEBULAE:
            positions.extend([0.0, 0.0, 0.0, 0.0])
            colors.extend([0.0, 0.0, 0.0, 0.0])
            
        return positions, colors
