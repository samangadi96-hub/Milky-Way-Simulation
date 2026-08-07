import math


class Camera:
    """
    Camera controlling the viewing perspective of the Milky Way simulation.
    """

    def __init__(self):

        # ==================================================
        # Camera Orientation
        # ==================================================

        # 0°  -> Face-on
        # 90° -> Edge-on
        self.inclination = math.radians(75.0)
        self.target_inclination = self.inclination

        # Rotation around galaxy (future)
        self.azimuth = 0.0
        self.target_azimuth = 0.0

        # Camera zoom (future)
        self.distance = 1.0
        self.target_distance = 1.0

        # Shader parameter
        self.disk_squish = math.cos(self.inclination)

    # ==================================================
    # Update Camera
    # ==================================================

    def update(self, dt):

        speed = 5.0

        # Smooth inclination
        self.inclination += (
            self.target_inclination -
            self.inclination
        ) * min(speed * dt, 1.0)

        # Smooth azimuth
        # self.azimuth += (
        #     self.target_azimuth -
        #     self.azimuth
        # ) * min(speed * dt, 1.0)

        # Smooth zoom
        self.distance += (
            self.target_distance -
            self.distance
        ) * min(speed * dt, 1.0)

        # Shader value
        self.disk_squish = max(
            0.02,
            math.cos(self.inclination)
        )

    # ==================================================
    # Inclination
    # ==================================================

    def look_up(self):

        self.target_inclination -= math.radians(5)

        self.target_inclination = max(
            0.0,
            self.target_inclination
        )

    def look_down(self):

        self.target_inclination += math.radians(5)

        self.target_inclination = min(
            math.radians(89.0),
            self.target_inclination
        )

    # ==================================================
    # Orbit (Future)
    # ==================================================

    def rotate_left(self, dt):

        self.azimuth -= math.radians(60) * dt

    def rotate_right(self, dt):

        self.azimuth += math.radians(60) * dt

    # ==================================================
    # Zoom (Future)
    # ==================================================

    def zoom_in(self):

        self.target_distance = max(
            0.3,
            self.target_distance - 0.02
        )

    def zoom_out(self):

        self.target_distance = min(
            10.0,
            self.target_distance + 0.02
        )