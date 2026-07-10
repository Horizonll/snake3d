"""游戏常量：网格、颜色、方向。"""

# 网格空间
GRID = 10          # 10x10x10 立方体空间
CELL = 1.0         # 每格世界尺寸
HALF = CELL / 2
ORIGIN_OFFSET = -(GRID * CELL) / 2  # 将网格中心对齐原点

# 六个移动方向 (dx, dy, dz)
DIRS = {
    "PX": (1, 0, 0),
    "NX": (-1, 0, 0),
    "PY": (0, 1, 0),
    "NY": (0, -1, 0),
    "PZ": (0, 0, 1),
    "NZ": (0, 0, -1),
}

# 方向反义表
OPPOSITE = {
    "PX": "NX", "NX": "PX",
    "PY": "NY", "NY": "PY",
    "PZ": "NZ", "NZ": "PZ",
}

# 渲染
FOV = 800        # 焦距（控制透视强度）
CLIP_NEAR = 0.5

# 颜色
SNAKE_HEAD_COLOR = "#00e5ff"
SNAKE_TAIL_COLOR = "#1a237e"
FOOD_COLOR = "#ff1744"
GRID_COLOR = "#1a3a5a"
BORDER_COLOR = "#4fc3f7"
BG_COLOR = "#0a0e1a"
TEXT_COLOR = "#e0f7fa"
ACCENT_COLOR = "#76ff03"
WRAP_BORDER_COLOR = "#76ff03"  # 穿墙模式边框色

# 墙壁模式
WALL_SOLID = "solid"  # 撞墙死
WALL_WRAP = "wrap"    # 穿墙从对面出来

# 视角模式
VIEW_FREE = 0     # 自由环绕原点
VIEW_FOLLOW = 1   # 第三人称跟随蛇头
VIEW_FPS = 2      # 第一人称（蛇头视角）
