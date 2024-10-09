#version 330 core

in vec3 in_vert;
in vec3 in_normal;

in vec3 in_offset;
in vec3 in_color;

uniform mat4 proj;
uniform mat4 mv;

out vec3 normal;
out vec3 pos;
out vec3 color;

void main(){
    vec4 pos_view =  mv * vec4(in_vert + in_offset, 1.0);
    gl_Position = proj * pos_view;

    mat3 m_normal = transpose(inverse(mat3(mv)));
    normal = m_normal * normalize(in_normal);
    pos = pos_view.xyz;
    color = in_color;
}