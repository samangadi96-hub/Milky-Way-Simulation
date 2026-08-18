import math
import random


class Galaxy:

    def __init__(self):

        # ==================================================
        # Galaxy Dimensions
        # ==================================================

        self.radius = 1.0
        self.disk_thickness = 0.15

        # ==================================================
        # Galactic Bulge
        # ==================================================

        self.bulge_radius = 0.20

        # ==================================================
        # Spiral Arms
        # ==================================================

        self.num_arms = 4
        self.arm_tightness = 4.0

    # ======================================================
    # Generate Star Position
    # ======================================================

    def generate_star_position(self):

        radius = random.uniform(
            0.0,
            self.radius
        )

        angle = random.uniform(
            0.0,
            2.0 * math.pi
        )

        x = radius * math.cos(angle)
        z = radius * math.sin(angle)

        y = random.uniform(
            -self.disk_thickness,
            self.disk_thickness
        )

        return x, y, z

    # ======================================================
    # Generate Spiral Star Position
    # ======================================================

    def generate_spiral_star_position(self):

        # Random distance from the center
        radius = random.uniform(
            self.bulge_radius,
            self.radius
        )

        # Pick one of the spiral arms
        arm = random.randrange(
            self.num_arms
        )

        # Base angle for the selected arm
        arm_angle = (
            2.0 * math.pi *
            arm /
            self.num_arms
        )

        # Spiral winding
        spiral_angle = (
            arm_angle +
            radius * self.arm_tightness
        )

        # Add randomness around the arm
        angle = (
            spiral_angle +
            random.gauss(0.0, 0.15)
        )

        # Convert to 3D coordinates
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)

        # Give the disk some thickness
        y = random.gauss(
            0.0,
            self.disk_thickness * 0.3
        )

        return x, y, z

    # ======================================================
    # Generate Multiple Stars
    # ======================================================

    def generate_stars(self, count):

        stars = []

        for _ in range(count):

            choice = random.random()

            # ==================================================
            # 1. CENTRAL BULGE
            # ==================================================

            if choice < 0.15:

                radius = random.uniform(
                    0.0,
                    self.bulge_radius
                )

                angle = random.uniform(
                    0.0,
                    2.0 * math.pi
                )

                x = radius * math.cos(angle)
                z = radius * math.sin(angle)

                y = random.gauss(
                    0.0,
                    self.disk_thickness * 0.5
                )

            #==================================================
            # 2. SPIRAL ARMS
            # ==================================================

            elif choice < 0.85:

                x, y, z = (
                    self.generate_spiral_star_position()
                )

            # ==================================================
            # 3. GENERAL DISK
            # ==================================================

            else:

                x, y, z = (
                    self.generate_star_position()
                )

            stars.append((x, y, z))

        return stars