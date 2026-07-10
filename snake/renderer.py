"""软件渲染器辅助：坐标转换、立方体生成、粒子系统。"""

import math
import random
from dataclasses import dataclass

from .math3d import vec_add, vec_scale
from .constants import CELL, HALF, ORIGIN_OFFSET, FOOD_COLOR


def grid_to_world(gx, gy, gz):
    """网格坐标 → 世界坐标中心点。"""
    return (
        gx * CELL + ORIGIN_OFFSET + HALF,
        gy * CELL + ORIGIN_OFFSET + HALF,
        gz * CELL + ORIGIN_OFFSET + HALF,
    )


def make_cube_faces(center, size=CELL):
    """生成立方体的 8 顶点 + 6 面 (顶点索引列表, 法线方向)。"""
    s = size / 2
    cx, cy, cz = center
    v = [
        (cx - s, cy - s, cz - s),  # 0
        (cx + s, cy - s, cz - s),  # 1
        (cx + s, cy + s, cz - s),  # 2
        (cx - s, cy + s, cz - s),  # 3
        (cx - s, cy - s, cz + s),  # 4
        (cx + s, cy - s, cz + s),  # 5
        (cx + s, cy + s, cz + s),  # 6
        (cx - s, cy + s, cz + s),  # 7
    ]
    faces = [
        ([0, 1, 2, 3], (0, 0, -1)),  # 后 (z-)
        ([5, 4, 7, 6], (0, 0, 1)),   # 前 (z+)
        ([4, 0, 3, 7], (-1, 0, 0)),  # 左 (x-)
        ([1, 5, 6, 2], (1, 0, 0)),   # 右 (x+)
        ([3, 2, 6, 7], (0, 1, 0)),   # 上 (y+)
        ([4, 5, 1, 0], (0, -1, 0)),  # 下 (y-)
    ]
    return v, faces


# -------------------- 粒子系统 --------------------

@dataclass
class Particle:
    pos: tuple
    vel: tuple
    life: float
    max_life: float
    color: str
    size: float = 0.15


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def burst(self, center, color=FOOD_COLOR, count=20):
        for _ in range(count):
            theta = random.uniform(0, math.tau)
            phi = random.uniform(0, math.pi)
            speed = random.uniform(1.5, 4.0)
            vel = (
                math.sin(phi) * math.cos(theta) * speed,
                math.sin(phi) * math.sin(theta) * speed,
                math.cos(phi) * speed,
            )
            life = random.uniform(0.4, 0.9)
            self.particles.append(Particle(center, vel, life, life, color))

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life > 0:
                p.pos = vec_add(p.pos, vec_scale(p.vel, dt))
                p.vel = vec_scale(p.vel, 1.0 - 2.0 * dt)  # 阻尼
                p.vel = (p.vel[0], p.vel[1] - 4.0 * dt, p.vel[2])  # 重力
                alive.append(p)
        self.particles = alive

    def is_empty(self):
        return len(self.particles) == 0
