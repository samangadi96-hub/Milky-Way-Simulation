class LODManager:
    """
    Determines which level of detail should be used
    based on the camera's distance from the object.
    """

    NEAR = 0
    MEDIUM = 1
    FAR = 2

    def __init__(self):
        # These values are temporary.
        # We will tune them later when the galaxy exists.
        self.near_distance = 2.0
        self.medium_distance = 6.0

    def get_level(self, distance):

        if distance < self.near_distance:
            return self.NEAR

        elif distance < self.medium_distance:
            return self.MEDIUM

        else:
            return self.FAR

    def get_level_name(self, level):

        if level == self.NEAR:
            return "NEAR"

        elif level == self.MEDIUM:
            return "MEDIUM"

        else:
            return "FAR"