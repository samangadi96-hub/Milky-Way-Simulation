import math


class Camera:
    """
    Camera controlling the viewing perspective of the Milky Way simulation.
    Supports smooth mouse-driven orbit (inclination + azimuth) with inertia,
    scroll-wheel zoom, and keyboard fallback controls.
    """

    # -----------------------------------------------------------------------
    # Tuning constants
    # -----------------------------------------------------------------------

    # Mouse sensitivity (radians per pixel)
    MOUSE_SENSITIVITY_X = 0.004   # azimuth (left-right)
    MOUSE_SENSITIVITY_Y = 0.004   # inclination (up-down)

    # How quickly the camera snaps to its target (easing speed)
    SMOOTH_SPEED = 8.0

    # Inertia: fraction of velocity kept each second when mouse is released
    # 1.0 = no damping, 0.0 = instant stop
    INERTIA_DECAY = 0.85          # ~85 % velocity kept per second
    INERTIA_STOP_THRESHOLD = 1e-5 # velocity magnitude below which we stop

    # Zoom
    ZOOM_STEP   = 0.08
    ZOOM_MIN    = 0.25
    ZOOM_MAX    = 8.0
    ZOOM_SMOOTH = 8.0

    # Keyboard orbit step (radians per call)
    KB_INCLINATION_STEP = math.radians(3)
    KB_AZIMUTH_SPEED    = math.radians(60)  # radians / second

    # Inclination limits
    INCL_MIN = 0.0
    INCL_MAX = math.radians(89.0)

    def __init__(self):

        # ------------------------------------------------------------------
        # Orientation state
        # ------------------------------------------------------------------
        # 0° → face-on view, 90° → edge-on view
        self.inclination        = math.radians(75.0)
        self.target_inclination = self.inclination

        self.azimuth        = 0.0
        self.target_azimuth = 0.0

        # ------------------------------------------------------------------
        # Zoom state
        # ------------------------------------------------------------------
        self.distance        = 1.0
        self.target_distance = 1.0

        # ------------------------------------------------------------------
        # Mouse drag state
        # ------------------------------------------------------------------
        self._dragging      = False
        self._last_mouse_x  = 0
        self._last_mouse_y  = 0

        # Angular velocity kept alive by inertia after drag ends
        self._vel_azimuth   = 0.0   # radians / second
        self._vel_inclination = 0.0  # radians / second

        # ------------------------------------------------------------------
        # Derived shader value
        # ------------------------------------------------------------------
        self.disk_squish = math.cos(self.inclination)

    # ==========================================================================
    # Mouse events  (call these from main.py)
    # ==========================================================================

    def on_mouse_press(self, x: int, y: int, button: int):
        """Begin a drag orbit when the left mouse button is pressed."""
        if button == 1:  # left button
            self._dragging      = True
            self._last_mouse_x  = x
            self._last_mouse_y  = y
            # Kill inertia when user grabs again
            self._vel_azimuth    = 0.0
            self._vel_inclination = 0.0

    def on_mouse_release(self, x: int, y: int, button: int):
        """End drag; inertia will coast the galaxy naturally."""
        if button == 1:
            self._dragging = False

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int):
        """
        Called every frame while any mouse button is held.
        dx / dy are pixel deltas since the last call.
        """
        if not self._dragging:
            return

        # Compute angular deltas
        d_azimuth    = -dx * self.MOUSE_SENSITIVITY_X
        d_inclination =  dy * self.MOUSE_SENSITIVITY_Y

        # Apply directly to the *targets* for instant but smooth response
        self.target_azimuth    += d_azimuth
        self.target_inclination = self._clamp_incl(
            self.target_inclination + d_inclination
        )

        # Store per-pixel velocity (converted to per-second in update)
        # We'll accumulate it here; _update_inertia divides by dt once
        self._vel_azimuth    = d_azimuth
        self._vel_inclination = d_inclination

        self._last_mouse_x = x
        self._last_mouse_y = y

    def on_mouse_scroll(self, x: int, y: int, x_offset: float, y_offset: float):
        """Scroll wheel zooms smoothly in/out."""
        self.target_distance -= y_offset * self.ZOOM_STEP
        self.target_distance  = max(self.ZOOM_MIN,
                                    min(self.ZOOM_MAX, self.target_distance))

    # ==========================================================================
    # Keyboard controls (unchanged API, kept for completeness)
    # ==========================================================================

    def look_up(self):
        self.target_inclination = self._clamp_incl(
            self.target_inclination - self.KB_INCLINATION_STEP
        )

    def look_down(self):
        self.target_inclination = self._clamp_incl(
            self.target_inclination + self.KB_INCLINATION_STEP
        )

    def rotate_left(self, dt: float):
        self.target_azimuth -= self.KB_AZIMUTH_SPEED * dt

    def rotate_right(self, dt: float):
        self.target_azimuth += self.KB_AZIMUTH_SPEED * dt

    def zoom_in(self):
        self.target_distance = max(self.ZOOM_MIN,
                                   self.target_distance - self.ZOOM_STEP)

    def zoom_out(self):
        self.target_distance = min(self.ZOOM_MAX,
                                   self.target_distance + self.ZOOM_STEP)

    # ==========================================================================
    # Per-frame update
    # ==========================================================================

    def update(self, dt: float):
        """Advance smooth interpolation and inertia. Call once per frame."""

        # ------------------------------------------------------------------
        # Inertia: coast the galaxy when not dragging
        # ------------------------------------------------------------------
        if not self._dragging:
            # Convert last-frame pixel delta → per-second velocity
            if dt > 0:
                vel_scale = 1.0 / dt  # delta was for one frame, scale to /s
            else:
                vel_scale = 0.0

            # Decay velocity exponentially
            decay = self.INERTIA_DECAY ** (dt * 60)  # frame-rate independent
            self._vel_azimuth    *= decay
            self._vel_inclination *= decay

            # Apply inertial movement to targets
            if abs(self._vel_azimuth) > self.INERTIA_STOP_THRESHOLD:
                self.target_azimuth += self._vel_azimuth
            else:
                self._vel_azimuth = 0.0

            if abs(self._vel_inclination) > self.INERTIA_STOP_THRESHOLD:
                self.target_inclination = self._clamp_incl(
                    self.target_inclination + self._vel_inclination
                )
            else:
                self._vel_inclination = 0.0

        # ------------------------------------------------------------------
        # Smooth exponential easing toward targets
        # ------------------------------------------------------------------
        t = min(self.SMOOTH_SPEED * dt, 1.0)

        self.inclination += (self.target_inclination - self.inclination) * t
        self.azimuth     += (self.target_azimuth     - self.azimuth)     * t
        self.distance    += (self.target_distance    - self.distance)     * min(self.ZOOM_SMOOTH * dt, 1.0)

        # ------------------------------------------------------------------
        # Derived value used by the black-hole shader
        # ------------------------------------------------------------------
        self.disk_squish = max(0.02, math.cos(self.inclination))

    # ==========================================================================
    # Internal helpers
    # ==========================================================================

    def _clamp_incl(self, v: float) -> float:
        return max(self.INCL_MIN, min(self.INCL_MAX, v))