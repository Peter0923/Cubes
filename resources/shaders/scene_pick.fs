#version 330 core
                
in float face_id;
in float instance_id;
in vec3 offset;

layout(location=0) out vec4 f_color0;
layout(location=1) out float f_color1;

void main(){
    f_color0 = vec4(offset, face_id);
    f_color1 = instance_id;
}