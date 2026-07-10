"""环绕场景的观察相机（lookAt 基向量模型 + 透视投影）。"""

import math
from dataclasses import dataclass, field

from .math3d import vec_sub, vec_dot, vec_cross, vec_norm
from .constants import FOV, CLIP_NEAR


@dataclass
class Camera:
    yaw: float = -0.6       # 水平旋转
    pitch: float = 0.35     # 垂直俯角
    distance: float = 28.0  # 距原点
    height: float = 4.0     # 垂直偏移
    auto_rotate: bool = True
    auto_speed: float = 0.15  # 弧度/秒
    _cached_basis: tuple = field(default=None, repr=False)

    def __post_init__(self):
        self._cached_basis = self._basis()

    def _basis(self):
        """计算相机基向量 (right, up, forward) 和位置。"""
        cp = math.cos(self.pitch)
        sp = math.sin(self.pitch)
        cy = math.cos(self.yaw)
        sy = math.sin(self.yaw)
        cam_pos = (
            self.distance * sy * cp,
            self.distance * sp + self.height,
            self.distance * cy * cp,
        )
        fwd = vec_norm((-cam_pos[0], -cam_pos[1], -cam_pos[2]))
        wup = (0.0, 1.0, 0.0)
        right = vec_norm(vec_cross(fwd, wup))
        up = vec_cross(right, fwd)
        return right, up, fwd, cam_pos

    def begin_frame(self):
        """每帧开始时缓存基向量，避免逐顶点重复计算。"""
        self._cached_basis = self._basis()

    def world_to_camera(self, p):
        """世界坐标 → 相机坐标。+Z 为深入屏幕方向。"""
        right, up, fwd, cam_pos = self._cached_basis
        rel = vec_sub(p, cam_pos)
        return (vec_dot(rel, right), vec_dot(rel, up), vec_dot(rel, fwd))

    def dir_to_camera(self, d):
        """世界方向/法线 → 相机空间方向（用于背面剔除与光照）。"""
        right, up, fwd, _ = self._cached_basis
        return (vec_dot(d, right), vec_dot(d, up), vec_dot(d, fwd))

    def project(self, p_cam, cx, cy):
        """相机坐标 → 屏幕坐标（透视投影）。"""
        z = p_cam[2]
        if z < CLIP_NEAR:
            z = CLIP_NEAR
        scale = FOV / z
        return (p_cam[0] * scale + cx, -p_cam[1] * scale + cy, z)

    def update(self, dt):
        if self.auto_rotate:
            self.yaw += self.auto_speed * dt
