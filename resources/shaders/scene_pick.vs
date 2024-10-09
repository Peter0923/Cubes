#version 330 core

in vec3 in_vert;
in vec3 in_offset;

uniform mat4 proj;
uniform mat4 mv;

out float face_id;
out float instance_id;
out vec3 offset;

void main(){ 
    gl_Position = proj * mv * vec4(in_vert + in_offset, 1.0);
    face_id = float(gl_VertexID / 6);
    instance_id = float(gl_InstanceID);
    offset = in_offset;
}