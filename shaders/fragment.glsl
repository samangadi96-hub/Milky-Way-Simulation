#version 330

uniform vec3 objectColor;
uniform int useGradient;   // 1 = photon ring, 2 = accretion disk, 3 = lensing halo
uniform float innerRadius;
uniform float outerRadius;
uniform float aspectRatio;
uniform float u_time;

in vec2 frag_pos;
out vec4 fragColor;

const float PI = 3.14159265359;

void main()
{
    vec2 corrected = vec2(frag_pos.x * aspectRatio, frag_pos.y);
    float dist = length(corrected);
    
    // Polar angle (-PI to PI)
    float angle = atan(corrected.y, corrected.x);

    // Universal Base colors
    vec3 inner_color = vec3(1.0, 0.6, 0.15);
    vec3 outer_color = vec3(0.4, 0.02, 0.0);

    if (useGradient == 1) {
        // --- Stage 3: Photon Ring ---
        float t = clamp((dist - innerRadius) / (outerRadius - innerRadius), 0.0, 1.0);
        vec3 color = mix(vec3(1.0, 0.85, 0.2), vec3(1.0, 0.3, 0.0), t);
        float alpha = smoothstep(1.0, 0.0, t);
        fragColor = vec4(color, alpha);

    } else if (useGradient == 2) {
        // --- Stage 5: Accretion Disk ---
        float t = clamp((dist - innerRadius) / (outerRadius - innerRadius), 0.0, 1.0);

        // Smooth continuous Keplerian rotation
        float speed = 0.3 / sqrt(max(dist, 0.01));
        float rotatedAngle = angle + u_time * speed;

        // Smooth organic spiral swirls (Fixes moiré pattern)
        float gas_density = 0.5 + 0.5 * sin(rotatedAngle * 5.0 + log(dist + 0.001) * 10.0);

        // Relativistic Doppler Beaming
        float doppler = 1.0 + 0.7 * cos(angle);

        vec3 color = mix(inner_color, outer_color, pow(t, 0.5));
        color *= (0.3 + 0.7 * gas_density) * doppler;

        // Soft edge blending
        float alpha = smoothstep(1.0, 0.0, pow(t, 0.4)) * 0.8;
        fragColor = vec4(color, alpha);

    } else if (useGradient == 3) {
        // --- Stage 6: Gravitational Lensing Halo ---
        float bend_dist = innerRadius + pow(innerRadius / max(dist, 0.001), 1.2) * (outerRadius - innerRadius);
        float t = clamp((bend_dist - innerRadius) / (outerRadius - innerRadius), 0.0, 1.0);

        float speed = 0.3 / sqrt(max(bend_dist, 0.01));
        float rotatedAngle = angle + u_time * speed;

        float gas_density = 0.5 + 0.5 * sin(rotatedAngle * 5.0 + log(bend_dist + 0.001) * 10.0);
        float doppler = 1.0 - 0.7 * cos(angle);

        vec3 color = mix(inner_color, outer_color, pow(t, 0.5));
        color *= (0.3 + 0.7 * gas_density) * doppler;

        // --- EQUATORIAL MASKING & BLENDING ---
        // Masks halo to vertical poles so it doesn't look like a background sphere
        float pole_mask = abs(sin(angle));
        float alpha = smoothstep(1.0, 0.0, t) * pow(pole_mask, 2.5) * 0.65;

        fragColor = vec4(color, alpha);

    } else {
        // --- Event Horizon ---
        fragColor = vec4(objectColor, 1.0);
    }
}