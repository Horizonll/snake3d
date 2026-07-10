"""3D 向量数学 + 颜色工具。"""

import math


# -------------------- 向量运算 --------------------

def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vec_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vec_len(a):
    return math.sqrt(vec_dot(a, a))


def vec_norm(a):
    l = vec_len(a)
    if l == 0:
        return (0, 0, 0)
    return vec_scale(a, 1.0 / l)


def vec_lerp(a, b, t):
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )


def rotate_x(p, angle):
    """绕 X 轴旋转（控制 pitch/俯仰）。"""
    c, s = math.cos(angle), math.sin(angle)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def rotate_y(p, angle):
    """绕 Y 轴旋转（控制 yaw/偏航）。"""
    c, s = math.cos(angle), math.sin(angle)
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


# -------------------- 颜色工具 --------------------

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % (
        max(0, min(255, rgb[0])),
        max(0, min(255, rgb[1])),
        max(0, min(255, rgb[2])),
    )


def shade_color(hex_color, brightness):
    """根据光照亮度调整颜色。brightness: 0.0~1.5"""
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex((
        int(r * brightness),
        int(g * brightness),
        int(b * brightness),
    ))


def lerp_color(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex((
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    ))
