#version 330

in vec2 uv;
out vec4 fragColor;

uniform sampler2D u_scene;
uniform sampler2D u_dust;
uniform sampler2D u_sceneDepth;
uniform bool u_debugDust;
uniform float u_nearPlane;
uniform float u_farPlane;

// Linearize a [0,1] depth buffer value to eye-space distance
float linearizeDepth(float d) {
    // d is in [0, 1] from the depth buffer
    float ndc_z = d * 2.0 - 1.0;  // [0,1] -> [-1,1]
    return (2.0 * u_nearPlane * u_farPlane) / (u_farPlane + u_nearPlane - ndc_z * (u_farPlane - u_nearPlane));
}

void main() {
    vec4 scene = texture(u_scene, uv);
    vec4 dust = texture(u_dust, uv);

    float transmittance = dust.r;
    float dustFrontDepthNorm = dust.g;  // normalized front dust depth (0 = no dust)

    if (u_debugDust) {
        // Debug: show dust transmittance as grayscale
        fragColor = vec4(transmittance, transmittance, transmittance, 1.0);
        return;
    }

    // Read scene depth
    float rawDepth = texture(u_sceneDepth, uv).r;

    // Check if there's actual dust at this pixel
    if (dustFrontDepthNorm < 0.001) {
        // No dust along this ray — pass through unchanged
        fragColor = vec4(scene.rgb, scene.a);
        return;
    }

    // Linearize depths
    float sceneLinearDepth = linearizeDepth(rawDepth);
    float dustFrontDepth = dustFrontDepthNorm * 200.0;  // decode from normalized

    // Depth comparison:
    // If the scene geometry (nearest star) is clearly IN FRONT of the dust,
    // don't attenuate it.
    // If the scene geometry is BEHIND the dust, apply full attenuation.
    // Smooth transition in between.

    // rawDepth ≈ 1.0 means no geometry wrote depth (clear value).
    // This could be:
    //   - Empty sky (should be attenuated — dust darkens background)
    //   - Black hole raymarcher output (protected by dust density=0 near center)
    // So we treat depth=1.0 as "very far behind dust" → apply attenuation.

    float depthFactor;
    if (rawDepth > 0.9999) {
        // No geometry depth — apply full dust attenuation
        // (BH is naturally protected because dust density = 0 at r < INNER_RADIUS)
        depthFactor = 1.0;
    } else {
        // Smooth transition: geometry in front of dust → less attenuation
        // geometry behind dust → full attenuation
        // Transition zone width controls the softness
        float transitionWidth = dustFrontDepth * 0.15 + 0.5;
        depthFactor = smoothstep(dustFrontDepth - transitionWidth, dustFrontDepth + transitionWidth * 0.3, sceneLinearDepth);
    }

    // Blend transmittance: 1.0 (no darkening) when in front, transmittance when behind
    float effectiveTransmittance = mix(1.0, transmittance, depthFactor);

    // Slight warm-neutral tint for attenuated light (realistic dust scattering)
    // Dust absorbs blue slightly more than red
    vec3 dustTint = mix(vec3(1.0), vec3(1.0, 0.97, 0.92), (1.0 - effectiveTransmittance) * 0.5);

    fragColor = vec4(scene.rgb * effectiveTransmittance * dustTint, scene.a);
}
