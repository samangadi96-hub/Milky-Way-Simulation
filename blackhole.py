import math


class BlackHole:
    def __init__(self,
                 radius=0.05,
                 aspect_ratio=1280 / 720):

        # Visual Properties
        self.event_horizon_radius = radius
        self.photon_sphere_radius = radius * 1.5
        self.inner_disk_radius = radius * 3.0
        self.outer_disk_radius = radius * 6.0

        # Camera Inclination (0° = Face-on, 90° = Edge-on)
        self.inclination = math.radians(83.0)
        self.target_inclination = self.inclination
        self.disk_squish = math.cos(self.inclination)

        self.aspect_ratio = aspect_ratio

    def update(self, delta_time):
        speed = 4.0
        self.inclination += (
            self.target_inclination - self.inclination
        ) * min(delta_time * speed, 1.0)

        # Convert inclination to apparent squish
        self.disk_squish = max(0.02, math.cos(self.inclination))