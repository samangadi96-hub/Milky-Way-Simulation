#version 330

in vec2 uv;
out vec4 fragColor;

uniform sampler2D u_scene;
uniform sampler2D u_dust;
uniform bool u_debugDust;

void main() {
    vec4 scene = texture(u_scene, uv);
    vec4 dust = texture(u_dust, uv);
    
    if (u_debugDust) {
        fragColor = vec4(dust.r, dust.r, dust.r, 1.0);
    } else {
        fragColor = vec4(scene.rgb * dust.r, scene.a);
    }
}
