#version 330

uniform float aspectRatio;
uniform float u_time;
uniform float u_diskSquish;
uniform float u_innerDisk;
uniform float u_outerDisk;
uniform float u_azimuth;
uniform float u_camDistance;
uniform float u_lodDetail;
uniform float u_volumetricDetail;
uniform float u_diskThickness;
uniform float u_proceduralStarWeight;
uniform float u_lodWeight;

in vec2 frag_pos;
out vec4 fragColor;

// ==========================================
// UTILITIES & NOISE
// ==========================================
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// 3D Hash for Volumetric Gas
float hash3D(vec3 p) {
    p = fract(p * vec3(0.1031, 0.1030, 0.0973));
    p += dot(p, p.yxz + 33.33);
    return fract((p.x + p.y) * p.z);
}

// 3D Noise function for gas turbulence
float noise3D(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    vec3 u = f * f * (3.0 - 2.0 * f);
    
    float n = mix(
        mix(mix(hash3D(i + vec3(0,0,0)), hash3D(i + vec3(1,0,0)), u.x),
            mix(hash3D(i + vec3(0,1,0)), hash3D(i + vec3(1,1,0)), u.x), u.y),
        mix(mix(hash3D(i + vec3(0,0,1)), hash3D(i + vec3(1,0,1)), u.x),
            mix(hash3D(i + vec3(0,1,1)), hash3D(i + vec3(1,1,1)), u.x), u.y), u.z);
    return n;
}

// 4-Octave 3D fBm
float fbm3D(vec3 p) {
    float f = 0.0;
    float amp = 0.5;
    for(int i = 0; i < 4; i++) {
        f += amp * noise3D(p);
        p *= 2.0;
        amp *= 0.5;
    }
    return f;
}

// --- PROCEDURAL STARFIELD ---
vec3 get_stars(vec2 p) {
    p += vec2(12.34, 56.78); 
    vec2 id = floor(p * 90.0);
    vec2 f = fract(p * 90.0);
    float star = smoothstep(0.96, 1.0, hash(id));
    star *= smoothstep(0.5, 0.1, length(f - 0.5));
    vec3 color = mix(vec3(0.6, 0.8, 1.0), vec3(1.0, 0.7, 0.4), hash(id + 1.0));
    return color * star * 4.0; 
}

void main()
{
    vec2 uv = vec2(frag_pos.x * aspectRatio, frag_pos.y);

    // 1. 3D CAMERA SETUP
    float Rs = 1.0;

    float cam_height = mix(0.1, 5.0, max(u_diskSquish, 0.02));
    float cam_radius = u_camDistance * 12.0;  // Scale the base distance of 12.0

    vec3 ray_origin = vec3(
        sin(u_azimuth) * cam_radius,
        cam_height,
        cos(u_azimuth) * cam_radius
    );

    vec3 forward = normalize(vec3(0.0) - ray_origin);
    vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), forward));
    vec3 up = cross(forward, right);

    float fov_zoom = 2.0; 
    vec3 ray_dir = normalize(forward * fov_zoom + uv.x * right + uv.y * up);

    // 2. PHYSICS ENGINE & VOLUMETRIC VARIABLES
    float dt = mix(0.2, 0.1, u_lodDetail);        
    int max_steps = int(mix(50.0, 300.0, u_lodDetail)); 
    
    vec3 p = ray_origin; 
    vec3 v = ray_dir;

    vec3 L = cross(p, v);
    float h2 = dot(L, L); 

    bool hit_black_hole = false;
    vec3 accumulated_gas_color = vec3(0.0);
    float transmittance = 1.0; // How much background light makes it through the gas

    // Gas Color Palette
    vec3 hot_white = vec3(1.0, 0.95, 0.8);
    vec3 bright_orange = vec3(1.0, 0.4, 0.05);
    vec3 dark_red = vec3(0.4, 0.05, 0.0);

    // 3. THE GEODESIC RAY-MARCHING LOOP
    for (int i = 0; i < max_steps; i++) {
        float r2 = dot(p, p);
        float r = sqrt(r2);

        if (r < Rs) {
            hit_black_hole = true;
            break;
        }

        if (r > cam_radius + 50.0) break; 

        // ==========================================
        // VOLUMETRIC ACCRETION DISK SAMPLING
        // ==========================================
        // Only calculate gas if we are near the equator and within the disk radius
        if (abs(p.y) < 0.5 && r > 2.5 && r < 12.0) {
            
            // Keplerian Rotation: inner gas orbits much faster than outer gas
            float orbital_velocity = 2.0 * pow(r, -1.5); 
            float angle = atan(p.z, p.x) + u_time * orbital_velocity;
            
            // Rotate the sampling coordinates to simulate fluid motion
            vec3 sampling_pos = vec3(r * cos(angle), p.y, r * sin(angle));

            // --------------------------------------------------
            // Thin galactic/accretion plane
            // --------------------------------------------------

            float disk_scale = max(
                u_diskThickness,
                0.08
            );

            float p_y_scaled =
                p.y / disk_scale;

            float vertical_falloff =
                exp(
                    -p_y_scaled *
                    p_y_scaled *
                    8.0
                );
            // --------------------------------------------------
            // Radial accretion-disk profile
            // --------------------------------------------------

            // Sharp inner edge, broad but soft outer falloff.
            float inner_edge = smoothstep(
                2.3,
                3.0,
                r
            );

            float outer_edge = 1.0 - smoothstep(
                7.0,
                10.5,
                r
            );

            // Concentrate the brightest material toward the centre.
            float radial_peak = exp(
                -pow((r - 3.8) / 2.4, 2.0)
            );

            float radial_falloff =
                inner_edge *
                outer_edge *
                (0.35 + 0.65 * radial_peak);
            
            // Apply 3D turbulent noise to the rotating volume
            float noise = fbm3D(sampling_pos * 1.5 - vec3(0.0, u_time * 0.2, 0.0));
            // Fade out noise as volumetric detail goes down
            noise = mix(1.0, noise, max(u_volumetricDetail, 0.01));
            
            // Keep the gas dense enough to glow,
            // but prevent the disk from becoming a solid wall.
            float density =
                vertical_falloff *
                radial_falloff *
                noise *
                0.85;

            // Make the inner disk denser than the outer disk.
            float inner_density_boost =
                smoothstep(7.0, 2.5, r);

            density *= mix(
                0.65,
                1.25,
                inner_density_boost
            );

            if (density > 0.05) {
                // ======================================================
                // COLOR / TEMPERATURE
                // ======================================================

                float temp = clamp(
                    1.0 - (r - 2.5) / 7.0,
                    0.0,
                    1.0
                );

                vec3 local_color = mix(
                    dark_red,
                    bright_orange,
                    temp
                );

                local_color = mix(
                    local_color,
                    hot_white,
                    pow(temp, 3.0)
                );


                // ======================================================
                // INNER DISK HEATING
                // ======================================================

                float inner_heat = smoothstep(
                    6.0,
                    2.5,
                    r
                );

                local_color *= mix(
                    0.65,
                    1.45,
                    inner_heat
                );


                // ======================================================
                // DOPPLER BEAMING
                // ======================================================

                float doppler =
                    1.0 +
                    0.8 *
                    (p.x / r) *
                    min(1.0, 5.0 / r);

                local_color *= pow(
                    doppler,
                    3.0
                );

                // ======================================================
                // DISK EMISSION
                // ======================================================

                // Emission should be bright, but spatially localized.
                const float EMISSION_STRENGTH = 1.35;

                float emission =
                    density *
                    EMISSION_STRENGTH;

                // Outer material is cooler and fainter.
                float outer_emission_fade =
                    1.0 - smoothstep(5.0, 10.0, r);

                emission *= mix(
                    0.35,
                    1.0,
                    outer_emission_fade
                );

                accumulated_gas_color +=
                    local_color *
                    emission *
                    dt *
                    transmittance;


                // ======================================================
                // DISK ABSORPTION / OPACITY
                // ======================================================

                // The disk absorbs much more gently than the old version.
                // This keeps background stars visible through low-density gas.
                // ======================================================
                // DISK TRANSMISSION
                // ======================================================

                // Emission and absorption are separate.
                // Dense gas blocks more background light.
                const float ABSORPTION_STRENGTH = 0.55;

                float optical_depth =
                    density *
                    dt *
                    ABSORPTION_STRENGTH;

                transmittance *= exp(-optical_depth);

                // Keep numerical stability.
                transmittance = clamp(
                    transmittance,
                    0.0,
                    1.0
                );
            }
        }

        // ==========================================
        // GENERAL RELATIVITY (Spacetime Curvature)
        // ==========================================
        
        // LOCAL 3-9 FIX ONLY
        // Distance-aware adaptive step size to bridge the empty space between the camera and the disk.
        // Active only when camera.distance is between 3.0 and 9.0.
        float current_dt = dt;
        float t_fix = smoothstep(2.8, 3.2, u_camDistance) * (1.0 - smoothstep(9.0, 10.5, u_camDistance));
        
        if (t_fix > 0.001 && r > 12.0) {
            float empty_space = max(0.0, cam_radius - 12.0);
            float safe_steps = max(20.0, float(max_steps) - 240.0); // leave 240 steps for the disk
            float max_boost = max(dt, empty_space / safe_steps);
            
            // Smoothly ramp down the boost as we approach the accretion disk (12.0 to 18.0)
            // to ensure we don't overshoot it.
            float approach_factor = smoothstep(12.0, 18.0, r);
            float boosted_dt = mix(dt, max_boost, approach_factor);
            
            // Apply the correction only based on how deep we are in the 3-9 range
            current_dt = mix(dt, boosted_dt, t_fix);
        }
        
        vec3 acceleration = -1.5 * Rs * h2 / (r2 * r2 * r) * p;
        v += acceleration * current_dt;
        v = normalize(v); 
        p += v * current_dt;
        
        // Early exit if the gas becomes completely opaque
        if (transmittance < 0.01) break; 
    }

    // ==========================================
    // FINAL COMPOSITING
    // ==========================================

    vec3 final_color = vec3(0.0);

    // --------------------------------------------------
    // Event horizon
    // --------------------------------------------------

    if (hit_black_hole)
    {
        // The event horizon is completely opaque.
        final_color = accumulated_gas_color;
        transmittance = 0.0;
    }
    else
    {
        // Background procedural stars.
        vec2 sky_uv = vec2(
            atan(v.z, v.x),
            asin(clamp(v.y, -1.0, 1.0))
        );

        vec3 background_stars =
            get_stars(sky_uv * 10.0) *
            u_proceduralStarWeight;

        final_color =
            accumulated_gas_color +
            background_stars * transmittance;
    }


    // ==========================================
    // LOD OUTPUT
    // ==========================================

    // Keep physical transmission separate from LOD fading.

    float final_alpha = mix(
        1.0,
        transmittance,
        u_lodWeight
    );

    vec3 final_rgb =
        final_color * u_lodWeight;

    fragColor = vec4(
        final_rgb,
        final_alpha
    );
    }