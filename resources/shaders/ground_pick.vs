#version 330 core

uniform mat4 proj;
uniform mat4 mv;

in vec3 in_vert;
in vec2 in_texCoord;

out vec2 texCoord; 

void main() {
    gl_Position = proj * mv * vec4(in_vert, 1.0);
    texCoord = in_texCoord;
}