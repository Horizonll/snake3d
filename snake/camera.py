"""观察相机（lookAt 基向量模型 + 透视投影）。

三种视角模式：
  VIEW_FREE   — 相机环绕原点（经典全局视角）
  VIEW_FOLLOW — 相机环绕蛇头位置（第三人称跟随）
  VIEW_FPS    — 相机在蛇头位置、朝向移动方向（第一人称蛇头视角）
"""

import math
from dataclasses import dataclass, field

from .math3d import vec_sub, vec_dot, vec_cross, vec_norm, vec_lerp, vec_add, vec_scale
from .constants import FOV, CLIP_NEAR, VIEW_FREE, VIEW_FOLLOW, VIEW_FPS, DIRS


@dataclass
class Camera:
    yaw: float = -0.6       # 水平旋转（FREE / FOLLOW 模式）
    pitch: float = 0.35     # 垂直俯角
    distance: float = 28.0  # 距目标点
    height: float = 4.0     # 垂直偏移
    auto_rotate: bool = True
    auto_speed: float = 0.15
    view_mode: int = VIEW_FREE
    # 目标点（蛇头世界坐标）
    _target: tuple = (0.0, 0.0, 0.0)
    _target_smooth: tuple = (0.0, 0.0, 0.0)
    # 蛇头移动方向（FPS 模式朝向）
    _head_dir: tuple = (1.0, 0.0, 0.0)
    _head_dir_smooth: tuple = (1.0, 0.0, 0.0)
    # FPS 模式的手动偏航/俯仰（相对蛇头方向）
    fps_yaw: float = 0.0
    fps_pitch: float = 0.0
    _cached_basis: tuple = field(default=None, repr=False)

    def __post_init__(self):
        self._target_smooth = self._target
        self._head_dir_smooth = self._head_dir
        self._cached_basis = self._basis()

    def set_target(self, pos):
        self._target = pos

    def set_head_dir(self, d):
        """设置蛇头移动方向（世界坐标向量）。"""
        self._head_dir = d

    def _basis(self):
        """计算相机基向量 (right, up, forward) 和位置。"""
        if self.view_mode == VIEW_FPS:
            return self._basis_fps()
        # FREE 和 FOLLOW 共用环绕逻辑，区别是目标点不同
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
        fwd = vec_norm(vec_sub(self._target_smooth, cam_pos))
        wup = (0.0, 1.0, 0.0)
        right = vec_norm(vec_cross(fwd, wup))
        up = vec_cross(right, fwd)
        return right, up, fwd, cam_pos

    def _basis_fps(self):
        """第一人称：相机在蛇头位置，朝向移动方向 + 手动偏航/俯仰。"""
        # 蛇头位置（略微抬高，避免被蛇身挡住）
        tx, ty, tz = self._target_smooth
        cam_pos = (tx, ty + 0.35, tz)

        # 基础朝向 = 蛇头移动方向
        base_fwd = vec_norm(self._head_dir_smooth)

        # 手动偏航：绕 Y 轴旋转
        cy = math.cos(self.fps_yaw)
        sy = math.sin(self.fps_yaw)
        fwd = (
            base_fwd[0] * cy + base_fwd[2] * sy,
            base_fwd[1],
            -base_fwd[0] * sy + base_fwd[2] * cy,
        )

        # 手动俯仰：绕 right 轴旋转
        wup = (0.0, 1.0, 0.0)
        right = vec_norm(vec_cross(fwd, wup))
        cp = math.cos(self.fps_pitch)
        sp = math.sin(self.fps_pitch)
        fwd = (
            fwd[0] * cp + right[0] * sp,
            fwd[1] * cp + right[1] * sp,
            fwd[2] * cp + right[2] * sp,
        )
        fwd = vec_norm(fwd)
        up = vec_cross(right, fwd)
        return right, up, fwd, cam_pos

    def begin_frame(self):
        self._cached_basis = self._basis()

    def world_to_camera(self, p):
        right, up, fwd, cam_pos = self._cached_basis
        rel = vec_sub(p, cam_pos)
        return (vec_dot(rel, right), vec_dot(rel, up), vec_dot(rel, fwd))

    def dir_to_camera(self, d):
        right, up, fwd, _ = self._cached_basis
        return (vec_dot(d, right), vec_dot(d, up), vec_dot(d, fwd))

    def project(self, p_cam, cx, cy):
        z = p_cam[2]
        if z < CLIP_NEAR:
            z = CLIP_NEAR
        scale = FOV / z
        return (p_cam[0] * scale + cx, -p_cam[1] * scale + cy, z)

    def update(self, dt):
        if self.view_mode == VIEW_FREE and self.auto_rotate:
            self.yaw += self.auto_speed * dt
        # 平滑插值
        lerp_t = min(1, dt * 8)
        self._target_smooth = vec_lerp(self._target_smooth, self._target, lerp_t)
        # 蛇头方向插值（球面近似——直接 lerp 再 norm）
        self._head_dir_smooth = vec_norm(vec_lerp(self._head_dir_smooth, self._head_dir, lerp_t))
