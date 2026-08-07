#version 330

uniform float aspectRatio;
uniform float u_time;
uniform float u_diskSquish;
uniform float u_innerDisk;
uniform float u_outerDisk;
uniform float u_azimuth;
uniform float u_camDistance;

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
    float dt = 0.1;        
    int max_steps = 300; 
    
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

            // Density calculation: Thicker in middle, falls off at edges
            float vertical_falloff = exp(-(p.y * p.y) * 20.0);
            float radial_falloff = smoothstep(2.5, 4.0, r) * (1.0 - smoothstep(8.0, 12.0, r));
            
            // Apply 3D turbulent noise to the rotating volume
            float noise = fbm3D(sampling_pos * 1.5 - vec3(0.0, u_time * 0.2, 0.0));
            float density = vertical_falloff * radial_falloff * noise * 2.5;

            if (density > 0.05) {
                // Color Gradient based on distance (Hotter near the black hole)
                float temp = clamp(1.0 - (r - 2.5) / 7.0, 0.0, 1.0);
                vec3 local_color = mix(dark_red, bright_orange, temp);
                local_color = mix(local_color, hot_white, pow(temp, 3.0));

                // Relativistic Doppler Beaming (Approximation)
                // Gas moving towards the camera is on the left (-x side generally)
                float doppler = 1.0 + 0.8 * (p.x / r) * min(1.0, 5.0/r); 
                local_color *= pow(doppler, 3.0); // Doppler boosts brightness exponentially

                // Accumulate the glowing gas
                accumulated_gas_color += local_color * density * dt * transmittance * 5.0;
                
                // The gas absorbs light behind it (makes the disk opaque)
                transmittance *= exp(-density * dt * 2.0);
            }
        }

        // ==========================================
        // GENERAL RELATIVITY (Spacetime Curvature)
        // ==========================================
        vec3 acceleration = -1.5 * Rs * h2 / (r2 * r2 * r) * p;
        v += acceleration * dt;
        v = normalize(v); 
        p += v * dt;
        
        // Early exit if the gas becomes completely opaque
        if (transmittance < 0.01) break; 
    }

    // 4. FINAL COMPOSITING
    vec3 final_color = vec3(0.0);

    if (hit_black_hole) {
        // Event horizon is pure black, but we add the gas we saw on the way in
        final_color = accumulated_gas_color; 
    } else {
        vec2 sky_uv = vec2(atan(v.z, v.x), asin(clamp(v.y, -1.0, 1.0)));
        vec3 background_stars = get_stars(sky_uv * 10.0);
        
        // We multiply the background stars by the transmittance (opacity) of the gas, 
        // then add the glowing gas on top. 
        final_color = (background_stars * transmittance) + accumulated_gas_color;
    }

    fragColor = vec4(final_color, 1.0);
}