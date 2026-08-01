class BlackHole:
    """
    Stores the physical and visual properties
    of the central supermassive black hole.
    """

    def __init__(
        self,
        radius=0.05,
        aspect_ratio=1280 / 720,
    ):

        # ==================================================
        # Physical Properties
        # ==================================================

        # Sagittarius A*
        self.mass = 4.154e6          # Solar masses

        # Kerr spin parameter (0 = Schwarzschild)
        self.spin = 0.0

        # ==================================================
        # Visual Properties
        # ==================================================

        self.event_horizon_radius = radius

        self.photon_sphere_radius = radius * 1.5

        self.inner_disk_radius = radius * 3.0

        self.outer_disk_radius = radius * 6.0

        # ==================================================
        # Rendering
        # ==================================================

        self.aspect_ratio = aspect_ratio