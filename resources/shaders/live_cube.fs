#version 330 core

in vec3 pos;
in vec3 normal;
in vec3 color;

out vec4 f_color;

void main(){
    float p = dot(normalize(-pos), normalize(normal));
    f_color = vec4(color * (0.25 + abs(p)*0.75), 1.0);
}