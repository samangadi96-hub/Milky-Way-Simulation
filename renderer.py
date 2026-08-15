from lod import LODManager


class Renderer:

    def __init__(
        self,
        ctx,
        program,
        main_quad_vao,
        galaxy_program,
        galaxy_vao,
        star_program,
        star_vao
    ):

        self.ctx = ctx

        # Black hole renderer
        self.program = program
        self.main_quad_vao = main_quad_vao

        # Galaxy renderer
        self.galaxy_program = galaxy_program
        self.galaxy_vao = galaxy_vao

        # Star renderer
        self.star_program = star_program
        self.star_vao = star_vao

    # ======================================================
    # Main Render
    # ======================================================

    def render(self, lod_level):

        # --------------------------------------------------
        # NEAR
        # --------------------------------------------------

        if lod_level == LODManager.NEAR:

            self.main_quad_vao.render(
                mode=self.ctx.TRIANGLE_STRIP
            )

        # --------------------------------------------------
        # MEDIUM
        # --------------------------------------------------

        elif lod_level == LODManager.MEDIUM:

            self.main_quad_vao.render(
                mode=self.ctx.TRIANGLE_STRIP
            )

        # --------------------------------------------------
        # FAR
        # --------------------------------------------------

        elif lod_level == LODManager.FAR:

            self.galaxy_vao.render(
                mode=self.ctx.TRIANGLE_STRIP
            )

    # ======================================================
    # Render Stars
    # ======================================================

    def render_stars(self, camera_distance):

        self.star_program["u_cameraDistance"].value = (
            camera_distance
        )

        self.ctx.point_size = 3.0

        self.star_vao.render(
            mode=self.ctx.POINTS
        )