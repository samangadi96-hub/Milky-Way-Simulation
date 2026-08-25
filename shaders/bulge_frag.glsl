#version 330

in vec3 v_color;
out vec4 fragColor;

void main() {
    // Render soft circular stars
    vec2 coord = gl_PointCoord * 2.0 - vec2(1.0);
    float r = length(coord);
    
    if (r > 1.0) {
        discard;
    }
    
    // Soft falloff for star glow
    float alpha = exp(-r * r * 4.0) * (1.0 - r);
    
    fragColor = vec4(v_color, alpha);
}
