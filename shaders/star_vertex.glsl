#version 330

in vec3 in_position;
in float in_brightness;
in float in_temperature;

out float starBrightness;
out float starTemperature;

uniform float u_cameraDistance;
uniform float u_inclination;
uniform float u_azimuth;

void main()
{
    vec3 position = in_position;

    // ======================================================
    // 1. Rotate around the galaxy
    // ======================================================

    float cosA = cos(u_azimuth);
    float sinA = sin(u_azimuth);

    float rotatedX =
        position.x * cosA -
        position.z * sinA;

    float rotatedZ =
        position.x * sinA +
        position.z * cosA;

    position.x = rotatedX;
    position.z = rotatedZ;

    // ======================================================
    // 2. Tilt the galaxy
    // ======================================================

    float cosI = cos(u_inclination);
    float sinI = sin(u_inclination);

    float rotatedY =
        position.y * cosI -
        position.z * sinI;

    float finalZ =
        position.y * sinI +
        position.z * cosI;

    position.y = rotatedY;
    position.z = finalZ;

    // ======================================================
    // 3. Camera distance / zoom
    // ======================================================

    float scale =
        6.0 / max(u_cameraDistance, 1.0);

    position *= scale;

    // ======================================================
    // 4. Pass stellar properties
    // ======================================================

    starBrightness = in_brightness;
    starTemperature = in_temperature;

    // ======================================================
    // 5. Projection
    // ======================================================

    gl_Position = vec4(
        position.x,
        position.z,
        0.0,
        1.0
    );

    // Slightly vary apparent star size
    gl_PointSize =
        1.5 +
        in_brightness * 3.0;
}