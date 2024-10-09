#version 330 core

uniform sampler2D image;                
in vec2 texCoord;
out vec4 f_color;

void main() {
    f_color = texture(image, texCoord);
}