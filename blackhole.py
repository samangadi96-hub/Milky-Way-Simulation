import numpy as np


class BlackHole:
    def __init__(self,
                 radius=0.05,
                 segments=100,
                 aspect_ratio=1280 / 720):

        # Physical Properties
        self.position = np.array([0.0, 0.0], dtype='f4')

        # Sagittarius A* (used later for physics)
        self.mass = 4.154e6  # Solar masses

        # Spin parameter (for future animation/lensing)
        self.spin = 0.0

        # Visual Properties
        self.event_horizon_radius = radius

        # Radius of the bright photon ring (widened for visible gradient)
        self.photon_sphere_radius = radius * 1.5

        # Accretion disk radii
        self.inner_disk_radius = radius * 3.0
        self.outer_disk_radius = radius * 6.0

        # Disk vertical squish (makes it look tilted in 3D)
        self.disk_squish = 0.12

        # Rendering
        self.segments = segments
        self.aspect_ratio = aspect_ratio

    # Generic circle generator
    def generate_circle(self, radius):
        vertices = []
        # Center vertex
        vertices.extend([0.0, 0.0])

        # Outer vertices
        for i in range(self.segments + 1):
            theta = 2 * np.pi * i / self.segments
            x = (radius * np.cos(theta)) / self.aspect_ratio
            y = radius * np.sin(theta)
            vertices.extend([x, y])

        return np.array(vertices, dtype='f4')

    # Event Horizon
    def generate_event_horizon(self):
        return self.generate_circle(self.event_horizon_radius)
    
    # Photon Sphere
    def generate_photon_sphere(self):
        return self.generate_circle(self.photon_sphere_radius)

    # Accretion Disk Base Radii
    def generate_inner_disk(self):
        return self.generate_circle(self.inner_disk_radius)

    def generate_outer_disk(self):
        return self.generate_circle(self.outer_disk_radius)
    
    # Annular disk (Ring) generator
    def generate_ring(self, inner_radius, outer_radius):
        vertices = []
        for i in range(self.segments + 1):
            theta = 2 * np.pi * i / self.segments
            # Outer circle
            x_outer = (outer_radius * np.cos(theta)) / self.aspect_ratio
            y_outer = outer_radius * np.sin(theta)
            # Inner circle
            x_inner = (inner_radius * np.cos(theta)) / self.aspect_ratio
            y_inner = inner_radius * np.sin(theta)
            
            # Triangle Strip
            vertices.extend([x_outer, y_outer])
            vertices.extend([x_inner, y_inner])

        return np.array(vertices, dtype='f4')
    
    def generate_photon_ring(self):
        return self.generate_ring(
            self.event_horizon_radius,
            self.photon_sphere_radius
        )

    # Accretion Disk — elliptical ring, squished vertically to fake 3D tilt
    def generate_accretion_disk(self):
        vertices = []
        for i in range(self.segments + 1):
            theta = 2 * np.pi * i / self.segments
            # Outer ellipse
            x_outer = (self.outer_disk_radius * np.cos(theta)) / self.aspect_ratio
            y_outer = self.outer_disk_radius * np.sin(theta) * self.disk_squish
            # Inner ellipse
            x_inner = (self.inner_disk_radius * np.cos(theta)) / self.aspect_ratio
            y_inner = self.inner_disk_radius * np.sin(theta) * self.disk_squish

            vertices.extend([x_outer, y_outer])
            vertices.extend([x_inner, y_inner])

        return np.array(vertices, dtype='f4')


# NEW: Gravitational Lensing Halo (Stage 6) - A full un-squished circular ring
    def generate_lensing_halo(self):
        return self.generate_ring(
            self.event_horizon_radius,
            self.outer_disk_radius * 0.8
        )