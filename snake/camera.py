"""环绕场景的观察相机（lookAt 基向量模型 + 透视投影）。

支持两种模式：
  - FREE：相机环绕原点（经典视角）
  - FOLLOW：相机环绕蛇头位置（跟随视角）
"""

import math
from dataclasses import dataclass, field

from .math3d import vec_sub, vec_dot, vec_cross, vec_norm, vec_lerp, vec_scale
from .constants import FOV, CLIP_NEAR


@dataclass
class Camera:
    yaw: float = -0.6       # 水平旋转
    pitch: float = 0.35     # 垂直俯角
    distance: float = 28.0  # 距目标点
    height: float = 4.0     # 垂直偏移
    auto_rotate: bool = True
    auto_speed: float = 0.15  # 弧度/秒
    follow: bool = False     # 是否跟随蛇头
    _target: tuple = (0.0, 0.0, 0.0)         # 当前看向的点（世界坐标）
    _target_smooth: tuple = (0.0, 0.0, 0.0)  # 平滑插值后的目标点
    _cached_basis: tuple = field(default=None, repr=False)

    def __post_init__(self):
        self._target_smooth = self._target
        self._cached_basis = self._basis()

    def set_target(self, pos):
        """设置相机看向的目标点（蛇头世界坐标）。"""
        self._target = pos

    def _basis(self):
        """计算相机基向量 (right, up, forward) 和位置。"""
        cp = math.cos(self.pitch)
        sp = math.sin(self.pitch)
        cy = math.cos(self.yaw)
        sy = math.sin(self.yaw)
        tx, ty, tz = self._target_smooth
        cam_pos = (
            self.distance * sy * cp + tx,
            self.distance * sp + self.height + ty,
            self.distance * cy * cp + tz,
        )
        # forward = 从相机指向目标
        fwd = vec_norm(vec_sub(self._target_smooth, cam_pos))
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
        # 平滑跟随目标
        if self.follow:
            self._target_smooth = vec_lerp(self._target_smooth, self._target, min(1, dt * 5))
