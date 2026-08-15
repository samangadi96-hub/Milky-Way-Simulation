#version 330

in vec3 in_position;

uniform float u_cameraDistance;


void main()
{
    vec3 position = in_position;

    // Simple galaxy-centered projection
    float scale = 1.0 / max(u_cameraDistance, 0.1);

    position *= scale;

    gl_Position = vec4(
        position.x,
        position.z,
        0.0,
        1.0
    );

    gl_PointSize = 3.0;
}