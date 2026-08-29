from lod import LODManager


class Renderer:

    def __init__(
        self,
        ctx,
        near_program,
        near_vao,
        medium_program,
        medium_vao,
        billboard_program,
        billboard_vao,
    ):
        self.ctx = ctx

        # Black-hole rendering programs
        self.near_program = near_program
        self.near_vao = near_vao

        self.medium_program = medium_program
        self.medium_vao = medium_vao

        self.billboard_program = billboard_program
        self.billboard_vao = billboard_vao

    # ==========================================================
    # BLACK HOLE / LOD RENDERING
    # ==========================================================

    def render(self, lod_state):
        """
        Render the appropriate black-hole LODs.

        The LOD manager provides continuous weights:
            near_weight
            medium_weight
            far_weight

        The transition regions may render more than one
        representation at the same time.
        """

        near_weight = float(lod_state["near_weight"])
        medium_weight = float(lod_state["medium_weight"])
        far_weight = float(lod_state["far_weight"])

        # ------------------------------------------------------
        # NEAR
        # ------------------------------------------------------
        if near_weight > 0.001:

            if "u_lodWeight" in self.near_program:
                self.near_program["u_lodWeight"].value = near_weight

            self.near_vao.render(
                mode=self.ctx.TRIANGLE_STRIP
            )

        # ------------------------------------------------------
        # MEDIUM
        # ------------------------------------------------------
        if medium_weight > 0.001:

            if "u_lodWeight" in self.medium_program:
                self.medium_program["u_lodWeight"].value = medium_weight

            self.medium_vao.render(
                mode=self.ctx.TRIANGLE_STRIP
            )

        # ------------------------------------------------------
        # FAR / BILLBOARD
        # ------------------------------------------------------
        if far_weight > 0.001:

            if "u_lodWeight" in self.billboard_program:
                self.billboard_program["u_lodWeight"].value = far_weight

            self.billboard_vao.render(
                mode=self.ctx.TRIANGLE_STRIP
            )