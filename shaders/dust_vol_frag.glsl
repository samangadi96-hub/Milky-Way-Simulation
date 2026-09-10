#version 330

in vec2 v_uv;
out vec4 fragColor;

uniform vec3 u_camPos;
uniform mat4 u_invVP;
uniform mat4 u_galaxyModel; // inverse rotation of galaxy
uniform float u_dustWeight;

// Tunable params
uniform float u_dustOpacity;
uniform float u_dustWidth;
uniform float u_dustArmOffset;
uniform float u_dustNoiseScale;
uniform float u_dustDensity;

// Hash and Noise functions for 3D procedural noise
float hash(vec3 p) {
    p = fract(p * 0.3183099 + 0.1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
    vec3 i = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(hash(i + vec3(0,0,0)), hash(i + vec3(1,0,0)), f.x),
                   mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
               mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x),
                   mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
}

float fbm(vec3 p) {
    float f = 0.0;
    float w = 0.5;
    for (int i = 0; i < 4; i++) {
        f += w * noise(p);
        p *= 2.0;
        w *= 0.5;
    }
    return f;
}

// Intersect a ray with a bounding slab y in [-H, H]
// Returns vec2(t_min, t_max)
vec2 intersectSlab(vec3 ro, vec3 rd, float H) {
    float t1 = (-H - ro.y) / rd.y;
    float t2 = (H - ro.y) / rd.y;
    float tmin = min(t1, t2);
    float tmax = max(t1, t2);
    tmin = max(0.0, tmin); // don't march behind camera
    return vec2(tmin, tmax);
}

// Galaxy parameters from galactic_disk.py
const float INNER_RADIUS = 2.0;
const float OUTER_RADIUS = 45.0;
const float ARM_COUNT = 4.0;
const float SPIRAL_TIGHTNESS = 2.5;

float getDustDensity(vec3 p) {
    // Distance to center
    float r = length(p.xz);
    if (r < INNER_RADIUS || r > OUTER_RADIUS) return 0.0;
    
    // Vertical falloff: exponential or gaussian
    float y_dist = abs(p.y);
    float vertical_falloff = exp(-y_dist * 5.0); 
    
    // Radial falloff (similar to stars)
    float radial_falloff = exp(-r / 8.0);
    
    // Spiral arm distance
    float theta = atan(p.z, p.x);
    
    // Find closest arm
    float min_dist = 100.0;
    for(int i = 0; i < int(ARM_COUNT); i++) {
        float arm_base_angle = float(i) * (2.0 * 3.14159265 / ARM_COUNT);
        float ideal_theta = arm_base_angle + SPIRAL_TIGHTNESS * log(r / INNER_RADIUS);
        
        // angular distance
        float d_theta = mod(theta - ideal_theta + 3.14159265, 2.0 * 3.14159265) - 3.14159265;
        float d_arm = abs(d_theta);
        min_dist = min(min_dist, d_arm);
    }
    
    // Dust is slightly offset from the star arm
    // Distance field in angle space: convert to approximate linear space by multiplying by r
    // However, since tightness is constant, angular offset works okay if tuned.
    float dust_dist = abs(min_dist - u_dustArmOffset);
    
    // Arm falloff
    float arm_factor = smoothstep(u_dustWidth, 0.0, dust_dist);
    
    // Irregularities / Noise
    float n1 = fbm(p * u_dustNoiseScale);
    float n2 = fbm(p * u_dustNoiseScale * 2.5 + vec3(12.3, 4.5, 6.7));
    
    // Combine noise into clumps and gaps
    float noise_val = n1 * n2;
    // Enhance contrast to make clumps denser and gaps emptier
    noise_val = smoothstep(0.05, 0.35, noise_val);
    
    float density = radial_falloff * vertical_falloff * arm_factor * noise_val * u_dustDensity;
    return density;
}

void main() {
    // 1. Reconstruct ray direction from Inverse VP
    vec2 ndc = v_uv * 2.0 - 1.0;
    vec4 target = u_invVP * vec4(ndc, 1.0, 1.0);
    vec3 rd = normalize(target.xyz / target.w - u_camPos);
    vec3 ro = u_camPos;
    
    // 2. Intersect with galactic slab
    float max_H = 1.0; // bounding height
    vec2 t_bounds = intersectSlab(ro, rd, max_H);
    
    float optical_depth = 0.0;
    
    if (t_bounds.y > t_bounds.x && u_dustWeight > 0.001) {
        float t = t_bounds.x;
        float t_end = min(t_bounds.y, 200.0); // max distance
        
        int steps = 32;
        float dt = (t_end - t) / float(steps);
        
        // Random jitter to hide banding
        float jitter = hash(vec3(ndc * 1000.0, 1.0));
        t += dt * jitter;
        
        for (int i = 0; i < steps; i++) {
            if (t > t_end) break;
            vec3 p = ro + rd * t;
            
            // Transform to galaxy local coordinates
            vec4 p_local = u_galaxyModel * vec4(p, 1.0);
            
            float dens = getDustDensity(p_local.xyz);
            optical_depth += dens * dt;
            
            t += dt;
        }
    }
    
    float transmittance = exp(-optical_depth * u_dustOpacity * u_dustWeight);
    fragColor = vec4(transmittance, transmittance, transmittance, 1.0);
}
