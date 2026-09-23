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
        
        # Emission colors (Realistic Astrophotography H-II palette)
        # H-alpha (656 nm, deep red) + H-beta (486 nm, blue-cyan) + O-III (500 nm, teal)
        color_hii_crimson = np.array([0.95, 0.05, 0.15]) # Pure deep H-alpha red
        color_hii_magenta = np.array([1.00, 0.15, 0.35]) # Standard H-II magenta/pink
        color_hii_salmon  = np.array([1.00, 0.30, 0.40]) # Warmer pink
        color_hii_pale    = np.array([1.00, 0.45, 0.55]) # Pale pink (mixed with O-III)
        
        # Blue/white for reflection nebulae (dust scattering hot young star light)
        color_ref_bright = np.array([0.4, 0.7, 1.0])
        color_ref_dusty  = np.array([0.2, 0.4, 0.8])
        
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
                c = color_ref_bright
                emission_strength = np.random.uniform(1.2, 2.0)
            elif ref_roll < 0.2: # 15% weak reflection / mixed
                c = color_ref_dusty * 0.4 + color_hii_magenta * 0.6
                emission_strength = np.random.uniform(1.0, 1.5)
            else: # 80% H-II
                c_roll = np.random.random()
                if c_roll < 0.30: c = color_hii_crimson
                elif c_roll < 0.70: c = color_hii_magenta
                elif c_roll < 0.90: c = color_hii_salmon
                else: c = color_hii_pale
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
            # Create dense star clusters (aggregates) that stand out from the surrounding disk
            if size_roll < 0.4: # Top 40% of nebulae get star clusters
                if size_roll < 0.1: # Hero regions get massive clusters
                    num_stars = np.random.randint(200, 500)
                elif size_roll < 0.25: # Medium regions get dense clusters
                    num_stars = np.random.randint(70, 150)
                else: # Smaller regions get sparse clusters
                    num_stars = np.random.randint(20, 50)
                    
                for _ in range(num_stars):
                    # Place star concentrated around the nebula core
                    dist_scale = np.random.gamma(shape=1.5, scale=0.3)
                    theta_star = np.random.uniform(0, 2 * np.pi)
                    phi_star = np.random.uniform(0, np.pi)
                    
                    # 3D offset (flattened slightly in the Y axis)
                    dx = radius * dist_scale * np.sin(phi_star) * np.cos(theta_star)
                    dy = (radius * dist_scale * np.cos(phi_star)) * 0.4
                    dz = radius * dist_scale * np.sin(phi_star) * np.sin(theta_star)
                    
                    sx = x + dx
                    sy = y + dy
                    sz = z + dz
                    
                    # Cluster star colors:
                    # Blend of extremely hot young blue stars, white giants, 
                    # and intensely colored stars matching the nebula gas to simulate unresolved glowing knots.
                    sc_roll = np.random.random()
                    if sc_roll < 0.3:
                        scolor = [0.7, 0.85, 1.0] # Bright young blue
                    elif sc_roll < 0.5:
                        scolor = [0.9, 0.95, 1.0] # Blue-white
                    elif sc_roll < 0.65:
                        scolor = [1.0, 1.0, 1.0] # Pure white
                    else:
                        # 35% of stars in the cluster take on the glowing gas color of the nebula itself
                        scolor = c 
                        
                    # Add subtle variance
                    scolor = np.clip(np.array(scolor) + np.random.normal(0, 0.05, 3), 0.0, 1.0)
                        
                    # Sizes and brightness
                    # A few very bright massive stars, mostly smaller cluster members
                    s_roll = np.random.random()
                    if s_roll < 0.02:
                        ssize = np.random.uniform(0.12, 0.25) # O-type giant
                        sbright = np.random.uniform(2.0, 3.5)
                    elif s_roll < 0.15:
                        ssize = np.random.uniform(0.06, 0.12) # B-type
                        sbright = np.random.uniform(1.2, 2.0)
                    else:
                        ssize = np.random.uniform(0.02, 0.05) # Standard cluster members
                        sbright = np.random.uniform(0.5, 1.0)
                    
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
