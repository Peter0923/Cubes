#version 330 core

uniform mat4 proj;
uniform mat4 mv;

in vec3 in_vert;

void main(){
    gl_Position = proj * mv * vec4(in_vert, 1.0);   
}