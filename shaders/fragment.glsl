#version 330

uniform vec3 objectColor;
uniform int useGradient;   // 1 = photon ring, 2 = accretion disk
uniform float innerRadius;
uniform float outerRadius;
uniform float aspectRatio;

in vec2 frag_pos;

out vec4 fragColor;

void main()
{
    if (useGradient == 1) {
        // --- Photon Ring: yellow -> orange -> transparent ---
        vec2 corrected = vec2(frag_pos.x * aspectRatio, frag_pos.y);
        float dist = length(corrected);

        float t = (dist - innerRadius) / (outerRadius - innerRadius);
        t = clamp(t, 0.0, 1.0);

        vec3 yellow = vec3(1.0, 0.85, 0.1);
        vec3 orange  = vec3(1.0, 0.3, 0.0);
        vec3 color = mix(yellow, orange, t);
        float alpha = smoothstep(1.0, 0.0, t);

        fragColor = vec4(color, alpha);

    } else if (useGradient == 2) {
        // --- Accretion Disk: warm orange -> deep red -> transparent ---
        vec2 corrected = vec2(frag_pos.x * aspectRatio, frag_pos.y);
        float dist = length(corrected);

        float t = (dist - innerRadius) / (outerRadius - innerRadius);
        t = clamp(t, 0.0, 1.0);

        // Softer orange inner edge, deep red outer edge
        vec3 inner_color = vec3(1.0, 0.55, 0.1);
        vec3 outer_color = vec3(0.5, 0.03, 0.0);
        vec3 color = mix(inner_color, outer_color, pow(t, 0.5));

        // Lower max alpha so photon ring stays visible on top
        float alpha = smoothstep(1.0, 0.0, pow(t, 0.4)) * 0.75;

        fragColor = vec4(color, alpha);

    } else {
        fragColor = vec4(objectColor, 1.0);
    }
}
