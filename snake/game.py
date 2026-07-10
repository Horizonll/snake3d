"""游戏逻辑状态 + tkinter 渲染主循环。

GameState 是纯逻辑（与渲染无关，可独立测试）。
Snake3DGame 负责 tkinter 窗口、输入、渲染。
"""

import math
import random
import tkinter as tk
from collections import deque
from dataclasses import dataclass, field

from .math3d import vec_lerp, vec_norm, vec_dot, shade_color, lerp_color
from .camera import Camera
from .renderer import ParticleSystem, grid_to_world, make_cube_faces
from .constants import (
    GRID, CELL, ORIGIN_OFFSET, DIRS, OPPOSITE, FOV, CLIP_NEAR,
    SNAKE_HEAD_COLOR, SNAKE_TAIL_COLOR, FOOD_COLOR, GRID_COLOR,
    BORDER_COLOR, BG_COLOR, TEXT_COLOR, ACCENT_COLOR, WRAP_BORDER_COLOR,
    WALL_SOLID, WALL_WRAP, VIEW_FREE, VIEW_FOLLOW, VIEW_FPS,
)


# ============================================================
# 游戏逻辑
# ============================================================

@dataclass
class GameState:
    """纯游戏逻辑状态（与渲染无关，可独立测试）。"""
    snake: deque = field(default_factory=deque)
    direction: str = "PX"
    pending_dir: str = "PX"
    food: tuple = (5, 5, 0)
    score: int = 0
    best: int = 0
    alive: bool = True
    paused: bool = False
    won: bool = False
    tick_accum: float = 0.0
    move_interval: float = 0.28
    grow_pending: int = 0
    wall_mode: str = WALL_WRAP  # 默认穿墙

    def reset(self):
        self.snake = deque()
        mid = GRID // 2
        for i in range(3):
            self.snake.append((mid - i, mid, 0))
        self.direction = "PX"
        self.pending_dir = "PX"
        self.score = 0
        self.alive = True
        self.paused = False
        self.won = False
        self.tick_accum = 0.0
        self.move_interval = 0.28
        self.grow_pending = 0
        self._spawn_food()

    @property
    def head(self):
        return self.snake[0]

    def _spawn_food(self):
        occupied = set(self.snake)
        free = [
            (x, y, z)
            for x in range(GRID)
            for y in range(GRID)
            for z in range(GRID)
            if (x, y, z) not in occupied
        ]
        if not free:
            self.won = True
            self.alive = False
            return
        self.food = random.choice(free)

    def set_direction(self, dir_name):
        """设置移动方向（禁止 180° 反转）。"""
        if not self.alive:
            return
        if dir_name == OPPOSITE.get(self.direction):
            return
        self.pending_dir = dir_name

    def step(self):
        """推进一步逻辑。返回 True 表示吃到食物。"""
        if not self.alive or self.paused or self.won:
            return False
        self.direction = self.pending_dir
        dx, dy, dz = DIRS[self.direction]
        hx, hy, hz = self.head
        nx, ny, nz = hx + dx, hy + dy, hz + dz

        # 边界处理
        if self.wall_mode == WALL_WRAP:
            nx = nx % GRID
            ny = ny % GRID
            nz = nz % GRID
        else:
            if not (0 <= nx < GRID and 0 <= ny < GRID and 0 <= nz < GRID):
                self.alive = False
                return False

        # 自碰
        body = list(self.snake)
        if self.grow_pending > 0:
            check_body = body
        else:
            check_body = body[:-1]
        if (nx, ny, nz) in set(check_body):
            self.alive = False
            return False

        self.snake.appendleft((nx, ny, nz))

        ate = False
        if (nx, ny, nz) == self.food:
            self.score += 1
            if self.score > self.best:
                self.best = self.score
            self.grow_pending += 1
            self.move_interval = max(0.10, 0.28 - self.score * 0.012)
            self._spawn_food()
            ate = True

        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.snake.pop()
        return ate

    def update(self, dt, on_eat=None):
        """时间驱动更新。"""
        if not self.alive or self.paused or self.won:
            return
        self.tick_accum += dt
        while self.tick_accum >= self.move_interval:
            self.tick_accum -= self.move_interval
            ate = self.step()
            if ate and on_eat:
                on_eat()


# ============================================================
# 主游戏（tkinter 渲染循环）
# ============================================================

class Snake3DGame:
    def __init__(self):
        self.state = GameState()
        self.state.reset()
        self.state.best = 0

        self.camera = Camera()
        self.particles = ParticleSystem()
        self.shake = 0.0
        self.flash = 0.0
        self.time = 0.0

        # 平滑插值
        self.prev_snake: list = list(self.state.snake)
        self.move_progress = 1.0

        # tkinter 窗口
        self.root = tk.Tk()
        self.root.title("3D Snake")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        self.W = 960
        self.H = 720
        self.canvas = tk.Canvas(
            self.root, width=self.W, height=self.H,
            bg=BG_COLOR, highlightthickness=0
        )
        self.canvas.pack()

        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)
        self.canvas.focus_set()

        self.keys_held = set()
        self.last_time = self._now()
        self._running = True

    def _now(self):
        return self.root.tk.call("clock", "milliseconds")

    # -------------------- 输入 --------------------

    def on_key_press(self, event):
        key = event.keysym.lower()
        self.keys_held.add(key)

        if key == "left":
            if self.camera.view_mode == VIEW_FPS:
                self.camera.fps_yaw -= 0.12
            else:
                self.camera.yaw -= 0.12
                self.camera.auto_rotate = False
        elif key == "right":
            if self.camera.view_mode == VIEW_FPS:
                self.camera.fps_yaw += 0.12
            else:
                self.camera.yaw += 0.12
                self.camera.auto_rotate = False
        elif key == "up":
            if self.camera.view_mode == VIEW_FPS:
                self.camera.fps_pitch = max(-0.6, self.camera.fps_pitch - 0.10)
            else:
                self.camera.pitch = max(-0.3, self.camera.pitch - 0.10)
        elif key == "down":
            if self.camera.view_mode == VIEW_FPS:
                self.camera.fps_pitch = min(0.6, self.camera.fps_pitch + 0.10)
            else:
                self.camera.pitch = min(1.0, self.camera.pitch + 0.10)
        elif key == "r":
            self.camera = Camera()
        elif key == "f":
            # 循环切换视角：FREE → FOLLOW → FPS → FREE
            modes = [VIEW_FREE, VIEW_FOLLOW, VIEW_FPS]
            idx = modes.index(self.camera.view_mode)
            self.camera.view_mode = modes[(idx + 1) % 3]
            self.camera.auto_rotate = self.camera.view_mode == VIEW_FREE
        elif key == "p":
            self.state.paused = not self.state.paused
        elif key == "t":
            # 切换穿墙模式（重启生效）
            self.state.wall_mode = (
                WALL_WRAP if self.state.wall_mode == WALL_SOLID else WALL_SOLID
            )
        elif key == "return":
            if not self.state.alive:
                self.state.reset()
                self.prev_snake = list(self.state.snake)
                self.move_progress = 1.0
                self.particles = ParticleSystem()
                self.shake = 0.0
                self.flash = 0.0
                self.time = 0.0
        elif key in ("w", "a", "s", "d", "space", "shift_l"):
            self._handle_move_key(key)

    def on_key_release(self, event):
        key = event.keysym.lower()
        self.keys_held.discard(key)

    def _handle_move_key(self, key):
        if not self.state.alive:
            return
        right, up, fwd, _ = self.camera._basis()
        fwd_xz = (fwd[0], fwd[2])
        right_xz = (right[0], right[2])

        def snap_axis(vec2):
            ax, az = vec2
            if abs(ax) > abs(az):
                return "PX" if ax > 0 else "NX"
            else:
                return "PZ" if az > 0 else "NZ"

        forward_axis = snap_axis(fwd_xz)
        right_axis = snap_axis(right_xz)

        dir_map = {
            "w": forward_axis,
            "s": OPPOSITE[forward_axis],
            "d": right_axis,
            "a": OPPOSITE[right_axis],
            "space": "PY",
            "shift_l": "NY",
        }
        d = dir_map.get(key)
        if d:
            self.state.set_direction(d)

    def _update_move_keys(self):
        for key in list(self.keys_held):
            if key in ("w", "a", "s", "d", "space", "shift_l"):
                self._handle_move_key(key)

    # -------------------- 游戏循环 --------------------

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self._loop()
        self.root.mainloop()

    def _quit(self):
        self._running = False
        self.root.destroy()

    def _loop(self):
        if not self._running:
            return
        now = self._now()
        dt = (now - self.last_time) / 1000.0
        self.last_time = now
        dt = min(dt, 0.05)

        self.update(dt)
        self.render()
        self.root.after(16, self._loop)

    def update(self, dt):
        self.time += dt
        self._update_move_keys()

        pre_snake = list(self.state.snake)

        def on_eat():
            world_pos = grid_to_world(*self.state.head)
            self.particles.burst(world_pos)
            self.flash = 0.3

        self.state.update(dt, on_eat=on_eat)

        if self.state.alive and not self.state.paused:
            self.move_progress = min(
                1.0, self.move_progress + dt / self.state.move_interval
            )

        if self.state.snake and (not pre_snake or self.state.snake[0] != pre_snake[0]):
            self.prev_snake = pre_snake
            self.move_progress = 0.0

        # 设置相机目标为蛇头渲染位置（含插值），再更新相机
        head_world = self._get_snake_render_positions()[0] if self.state.snake else (0, 0, 0)
        self.camera.set_target(head_world)
        # 传递蛇头移动方向（FPS 模式朝向）
        head_dir = DIRS.get(self.state.direction, (1, 0, 0))
        self.camera.set_head_dir(head_dir)
        self.camera.update(dt)
        self.camera.begin_frame()

        self.particles.update(dt)
        if self.shake > 0:
            self.shake = max(0, self.shake - dt * 4)
        if self.flash > 0:
            self.flash = max(0, self.flash - dt * 3)

        if not self.state.alive and self.shake == 0 and not self.state.won:
            self.shake = 1.0

    # -------------------- 渲染 --------------------

    def render(self):
        c = self.canvas
        c.delete("all")

        shake_x = shake_y = 0
        if self.shake > 0:
            shake_x = random.uniform(-1, 1) * self.shake * 8
            shake_y = random.uniform(-1, 1) * self.shake * 8

        cx = self.W / 2 + shake_x
        cy = self.H / 2 + shake_y
        cam = self.camera

        render_faces = []

        self._render_grid_box(render_faces, cam)
        self._render_snake(render_faces, cam)
        if self.state.alive and not self.state.won:
            self._render_food(render_faces, cam)
        self._render_particles(render_faces, cam)

        render_faces.sort(key=lambda f: -f["depth"])

        for face in render_faces:
            if face["type"] == "polygon":
                pts = []
                for p in face["cam_pts"]:
                    sx, sy, sz = cam.project(p, cx, cy)
                    pts.extend([sx, sy])
                c.create_polygon(
                    pts, fill=face["fill"], outline=face["outline"],
                    width=face.get("width", 1), tags="frame",
                )
            elif face["type"] == "line":
                p1 = cam.project(face["p1"], cx, cy)
                p2 = cam.project(face["p2"], cx, cy)
                c.create_line(
                    p1[0], p1[1], p2[0], p2[1],
                    fill=face["fill"], width=face.get("width", 1), tags="frame",
                )

        self._render_ui()

    def _render_grid_box(self, render_faces, cam):
        s = GRID * CELL / 2
        corners = [
            (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s),
            (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s),
        ]
        cam_corners = [cam.world_to_camera(p) for p in corners]

        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]

        border_color = (
            WRAP_BORDER_COLOR if self.state.wall_mode == WALL_WRAP else BORDER_COLOR
        )

        for i, j in edges:
            p1 = cam_corners[i]
            p2 = cam_corners[j]
            depth = (p1[2] + p2[2]) / 2
            render_faces.append({
                "type": "line", "p1": p1, "p2": p2,
                "depth": depth, "fill": border_color, "width": 2,
            })

        for i in range(0, GRID + 1):
            t = ORIGIN_OFFSET + i * CELL
            p1 = cam.world_to_camera((ORIGIN_OFFSET, -s, t))
            p2 = cam.world_to_camera((s, -s, t))
            render_faces.append({
                "type": "line", "p1": p1, "p2": p2,
                "depth": (p1[2] + p2[2]) / 2,
                "fill": GRID_COLOR, "width": 1,
            })
            p1 = cam.world_to_camera((t, -s, ORIGIN_OFFSET))
            p2 = cam.world_to_camera((t, -s, s))
            render_faces.append({
                "type": "line", "p1": p1, "p2": p2,
                "depth": (p1[2] + p2[2]) / 2,
                "fill": GRID_COLOR, "width": 1,
            })

    def _get_snake_render_positions(self):
        """获取蛇身渲染位置（带插值，支持穿墙分段）。"""
        positions = []
        snake = list(self.state.snake)
        prev = self.prev_snake
        t = 1.0 if not self.state.alive else self.move_progress

        for i, seg in enumerate(snake):
            if prev and i < len(prev):
                p_prev = grid_to_world(*prev[i])
            elif prev and i == len(prev):
                p_prev = grid_to_world(*prev[0])
            else:
                p_prev = grid_to_world(*seg)

            p_curr = grid_to_world(*seg)

            # 穿墙检测：如果 prev 和 curr 跨越了边界（距离 > 1 格），
            # 说明发生了环绕，需要分段渲染
            dist = math.sqrt(
                (p_prev[0] - p_curr[0]) ** 2
                + (p_prev[1] - p_curr[1]) ** 2
                + (p_prev[2] - p_curr[2]) ** 2
            )

            if dist > CELL * 1.5:
                # 穿墙：用两段表示（出墙 + 进墙），这里简化为直接跳到 curr
                # （完整分段需额外渲染管道，此处保持当前位置避免视觉撕裂）
                pos = p_curr
            else:
                pos = vec_lerp(p_prev, p_curr, t)

            positions.append(pos)
        return positions

    def _render_snake(self, render_faces, cam):
        positions = self._get_snake_render_positions()
        n = len(positions)

        for i, pos in enumerate(positions):
            t_ratio = i / max(1, n - 1)
            color = lerp_color(SNAKE_HEAD_COLOR, SNAKE_TAIL_COLOR, t_ratio)
            size = CELL * 0.95 if i == 0 else CELL * 0.88

            verts, faces = make_cube_faces(pos, size)
            cam_verts = [cam.world_to_camera(v) for v in verts]

            for indices, normal in faces:
                cam_pts = [cam_verts[idx] for idx in indices]
                depth = sum(p[2] for p in cam_pts) / len(cam_pts)
                n_cam = cam.dir_to_camera(normal)

                if n_cam[2] < 0:
                    light = vec_norm((0.3, 0.8, -0.5))
                    brightness = max(0.35, abs(vec_dot(n_cam, light)) * 0.8 + 0.4)
                    fill = shade_color(color, brightness)
                    outline = shade_color(color, brightness * 0.6)
                    render_faces.append({
                        "type": "polygon",
                        "cam_pts": cam_pts,
                        "depth": depth,
                        "fill": fill, "outline": outline, "width": 1,
                    })

    def _render_food(self, render_faces, cam):
        pulse = 0.85 + 0.15 * math.sin(self.time * 6)
        size = CELL * 0.6 * pulse
        pos = grid_to_world(*self.state.food)
        verts, faces = make_cube_faces(pos, size)
        cam_verts = [cam.world_to_camera(v) for v in verts]
        glow = 0.7 + 0.3 * math.sin(self.time * 6)

        for indices, normal in faces:
            cam_pts = [cam_verts[idx] for idx in indices]
            depth = sum(p[2] for p in cam_pts) / len(cam_pts)
            n_cam = cam.dir_to_camera(normal)
            if n_cam[2] < 0:
                brightness = max(0.5, abs(n_cam[2]) * glow + 0.5)
                fill = shade_color(FOOD_COLOR, brightness)
                outline = shade_color(FOOD_COLOR, brightness * 1.2)
                render_faces.append({
                    "type": "polygon",
                    "cam_pts": cam_pts,
                    "depth": depth,
                    "fill": fill, "outline": outline, "width": 1,
                })

    def _render_particles(self, render_faces, cam):
        for p in self.particles.particles:
            alpha = p.life / p.max_life
            size = p.size * (0.5 + alpha * 0.5)
            pos_cam = cam.world_to_camera(p.pos)
            if pos_cam[2] < CLIP_NEAR:
                continue
            sx, sy, sz = cam.project(pos_cam, self.W / 2, self.H / 2)
            r = max(1, size * FOV / sz * 0.5)
            color = shade_color(p.color, alpha)
            render_faces.append({
                "type": "polygon",
                "cam_pts": self._make_quad_cam(pos_cam, r),
                "depth": pos_cam[2],
                "fill": color, "outline": "", "width": 0,
            })

    def _make_quad_cam(self, center_cam, half_size):
        cx, cy, cz = center_cam
        return [
            (cx - half_size, cy - half_size, cz),
            (cx + half_size, cy - half_size, cz),
            (cx + half_size, cy + half_size, cz),
            (cx - half_size, cy + half_size, cz),
        ]

    def _render_ui(self):
        c = self.canvas

        # 闪光
        if self.flash > 0:
            flash_fill = lerp_color(BG_COLOR, ACCENT_COLOR, self.flash * 0.15)
            c.create_rectangle(0, 0, self.W, self.H,
                               fill=flash_fill, outline="", tags="frame")
            c.create_text(self.W // 2, self.H // 2 - 80,
                          text="+1", fill=ACCENT_COLOR,
                          font=("Consolas", 36, "bold"), tags="frame")

        # 分数
        c.create_text(20, 20, anchor="nw",
                      text=f"SCORE  {self.state.score}",
                      fill=TEXT_COLOR, font=("Consolas", 20, "bold"), tags="frame")
        c.create_text(20, 48, anchor="nw",
                      text=f"BEST   {self.state.best}",
                      fill="#80deea", font=("Consolas", 14), tags="frame")
        c.create_text(20, 70, anchor="nw",
                      text=f"LEN    {len(self.state.snake)}",
                      fill="#80deea", font=("Consolas", 14), tags="frame")

        # 模式指示
        mode_text = "WRAP" if self.state.wall_mode == WALL_WRAP else "SOLID"
        mode_color = WRAP_BORDER_COLOR if self.state.wall_mode == WALL_WRAP else BORDER_COLOR
        c.create_text(20, 92, anchor="nw",
                      text=f"WALL   {mode_text}",
                      fill=mode_color, font=("Consolas", 14), tags="frame")

        # 视角指示
        view_names = {VIEW_FREE: "FREE", VIEW_FOLLOW: "FOLLOW", VIEW_FPS: "FPS"}
        view_text = view_names.get(self.camera.view_mode, "?")
        c.create_text(20, 114, anchor="nw",
                      text=f"VIEW   {view_text}",
                      fill=ACCENT_COLOR, font=("Consolas", 14), tags="frame")

        # 操作提示
        hint = "WASD move | Arrows cam | R reset | F view | P pause | T wall | Enter restart"
        c.create_text(self.W - 20, 20, anchor="ne", text=hint,
                      fill="#546e7a", font=("Consolas", 11), tags="frame")

        # 暂停
        if self.state.paused and self.state.alive:
            c.create_text(self.W // 2, self.H // 2, text="PAUSED",
                          fill=TEXT_COLOR, font=("Consolas", 48, "bold"), tags="frame")
            c.create_text(self.W // 2, self.H // 2 + 40, text="Press P to resume",
                          fill="#80deea", font=("Consolas", 16), tags="frame")

        # 游戏结束
        if not self.state.alive:
            if self.state.won:
                c.create_text(self.W // 2, self.H // 2 - 30,
                              text="YOU WIN!", fill=ACCENT_COLOR,
                              font=("Consolas", 56, "bold"), tags="frame")
                c.create_text(self.W // 2, self.H // 2 + 20,
                              text=f"Final Score: {self.state.score}",
                              fill=TEXT_COLOR, font=("Consolas", 20), tags="frame")
            else:
                c.create_text(self.W // 2, self.H // 2 - 30,
                              text="GAME OVER", fill=FOOD_COLOR,
                              font=("Consolas", 56, "bold"), tags="frame")
                c.create_text(self.W // 2, self.H // 2 + 20,
                              text=f"Score: {self.state.score}",
                              fill=TEXT_COLOR, font=("Consolas", 20), tags="frame")
            c.create_text(self.W // 2, self.H // 2 + 60,
                          text="Press ENTER to restart",
                          fill="#80deea", font=("Consolas", 16), tags="frame")
