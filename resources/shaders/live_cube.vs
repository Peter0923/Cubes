#version 330 core

in vec3 in_vert;
in vec3 in_normal;

in vec3 in_offset;
in vec3 in_dir;
in vec3 in_color;

uniform mat4 proj;
uniform mat4 mv;
uniform float time;

out vec3 normal;
out vec3 pos;
out vec3 color;

void main(){
    // vec3 move = 5.0 * vec3(sin(time), cos(time), 0.0);
    vec3 move = (1.0 - sin(time)) * in_dir;
    vec4 pos_view =  mv * vec4(in_vert + in_offset + move, 1.0);
    gl_Position = proj * pos_view;

    mat3 m_normal = transpose(inverse(mat3(mv)));
    normal = m_normal * normalize(in_normal);
    pos = pos_view.xyz;
    color = in_color;
}