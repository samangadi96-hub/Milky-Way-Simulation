#version 330

uniform float aspectRatio;
uniform float u_time;
uniform float u_eventHorizon;
uniform float u_photonSphere;
uniform float u_innerDisk;
uniform float u_outerDisk;
uniform float u_diskSquish;

in vec2 frag_pos;
out vec4 fragColor;

// Smooth hash - no grid artifacts
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}



// fBm with 4 octaves for richer gas detail
float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}

// Swirling gas sampled in polar coords with Keplerian rotation.
float swirling_gas(float angle, float dist, float time_offset) {
    // Keplerian angular velocity: inner gas orbits faster
    float orbital_speed = 1.0 / pow(max(dist, 0.01), 1.5);
    float rotated_angle = angle + u_time * orbital_speed + time_offset;

    // Increased angular frequency and inward accretion drift for visible motion
    vec2 polar_uv = vec2(rotated_angle * 1.8, dist * 7.0 - u_time * 0.3);
    return fbm(polar_uv);
}

void main()
{
    vec2 uv = vec2(frag_pos.x * aspectRatio, frag_pos.y);

float dist = length(uv);
float angle = atan(uv.y, uv.x);

// ===================================================
// Dynamic camera inclination
//
// u_diskSquish:
// 1.0  = face-on
// 0.02 = edge-on
// ===================================================
float y_local = abs(uv.y) / max(u_diskSquish, 0.02);
    float r_eh  = u_eventHorizon;
    float r_ps  = u_photonSphere;
    float r_in  = u_innerDisk;
    float r_out = u_outerDisk;

    // ---- EVENT HORIZON: solid opaque black ----
    if (dist < r_eh) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }



    vec3 hot_white     = vec3(1.0, 0.96, 0.88);
    vec3 bright_orange = vec3(1.0, 0.55, 0.05);
    vec3 deep_orange   = vec3(0.85, 0.30, 0.0);
    vec3 dark_red      = vec3(0.35, 0.08, 0.0);

    vec3 total = vec3(0.0);

    // Soft fade just outside the event horizon edge
    float eh_fade = smoothstep(r_eh, r_eh * 1.08, dist);

    // ---- UNIFIED DENSITY FIELD ----

    // A) Equatorial disk density (Gaussian vertical profile)
    float thickness = mix(
    0.015,
    0.04,
    clamp((dist - r_in) / (r_out - r_in), 0.0, 1.0)
);

float disk_vert = exp(
    -(y_local * y_local) /
    (2.0 * thickness * thickness)
);

    float radial_t = clamp((dist - r_in) / (r_out - r_in), 0.0, 1.0);
    float disk_radial = smoothstep(r_in * 0.8, r_in * 1.05, dist)
                      * (1.0 - smoothstep(r_out * 0.75, r_out * 1.15, dist));
    disk_radial = pow(disk_radial, 0.45);

    float disk_density = disk_vert * disk_radial * eh_fade;

    // B) Lensing halo density (broad circular glow)
    float halo_width = (r_out - r_eh) * 0.35;
    float halo_center = r_ps * 1.2;
    float halo_r = dist - halo_center;
    float halo_radial = exp(-(halo_r * halo_r) / (2.0 * halo_width * halo_width));
    halo_radial *= smoothstep(r_eh, r_eh * 1.2, dist);
    halo_radial *= 1.0 - smoothstep(r_out * 0.7, r_out * 1.3, dist);

    // Suppress halo where disk is already bright (seamless melt)
    float halo_density = halo_radial * (1.0 - disk_density * 0.8) * eh_fade * 0.55;

    // C) Combined gas density
    float total_density = disk_density + halo_density;

    if (total_density > 0.005) {
        float disk_weight = disk_density / max(total_density, 0.001);

        // ---- KEPLERIAN GAS MOTION ----
        float disk_gas = swirling_gas(angle, dist, 0.0);
        float halo_gas = swirling_gas(-angle, dist, 3.14);

        // Blend the two gas patterns based on which component dominates
        float gas = mix(halo_gas, disk_gas, disk_weight);

        // ---- DOPPLER BEAMING (time-coupled) ----
        float disk_doppler = 1.0 + 0.4 * cos(angle);
        float halo_doppler = 1.0 - 0.25 * cos(angle);
        float doppler = mix(halo_doppler, disk_doppler, disk_weight);

        // Color gradient (hot near center, cool at edge)
        float color_t = clamp((dist - r_eh) / (r_out - r_eh), 0.0, 1.0);
        vec3 color = mix(deep_orange, dark_red, pow(color_t, 0.5));

        // White-hot boost on Doppler peaks near inner edge
        float white_blend = smoothstep(1.15, 1.4, doppler) * (1.0 - color_t) * 0.7;
        color = mix(color, hot_white, white_blend);

        // Strong gas modulation for visible swirling movement
        float gas_mod = 0.35 + 1.30 * gas;
        color *= gas_mod * doppler;

        total += color * (total_density * gas_mod);
    }

    // ---- PHOTON RING with shimmer ----
    {
        float ring_r = (r_eh + r_ps) * 0.52;
        float ring_w = (r_ps - r_eh) * 0.12;
        float d = abs(dist - ring_r);

        float peak = exp(-(d * d) / (2.0 * ring_w * ring_w));
        float glow = exp(-(d * d) / (2.0 * (ring_w * 6.0) * (ring_w * 6.0))) * 0.12;

        float shimmer_speed = 8.0;
        float shimmer = 0.92 + 0.08 * sin(angle * 3.0 + u_time * shimmer_speed)
                                    * sin(angle * 5.0 - u_time * shimmer_speed * 0.7);

        float intensity = (peak + glow) * eh_fade * shimmer;

        vec3 ring_color = mix(bright_orange, hot_white, peak);
        total += ring_color * intensity;
    }

    // ---- FINAL COMPOSITING ----
    // Output to the Framebuffer (FBO) for your Bloom pass
    fragColor = vec4(total, 1.0);
}