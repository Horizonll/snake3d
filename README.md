# 3D Snake

3D 贪吃蛇游戏 — 纯标准库/零依赖实现，同时提供桌面版和 Web 版。

## 在线玩

push 到 main 自动部署 GitHub Pages：

> https://horizonll.github.io/snake3d/

## 本地运行

### Web 版（浏览器）
直接用浏览器打开 `web/index.html`，或启动本地服务器：
```bash
python -m http.server 8765 --directory web
```
访问 http://localhost:8765

### 桌面版（tkinter）
```bash
uv run python main.py
```

## 操作

| 按键 | 功能 |
|------|------|
| W / S | 前进 / 后退（相对摄像机方向） |
| A / D | 左 / 右 |
| Space / Shift | 上升 / 下降 |
| 方向键 | 旋转摄像机视角 |
| R | 重置摄像机 |
| P | 暂停 / 继续 |
| T | 切换穿墙 / 撞墙模式 |
| Enter | 重新开始（游戏结束后） |

移动端：使用屏幕底部触控按钮

## 游戏模式

- **WRAP（穿墙）**：蛇头穿越墙壁从对面出现，默认模式，边框显示绿色
- **SOLID（撞墙）**：撞墙即死，经典模式，边框显示蓝色
- 按 T 实时切换

## 项目结构

```
snake/
├── main.py              # 桌面版入口
├── web/
│   └── index.html       # Web 版（单文件，零依赖）
├── snake/               # Python 桌面版包
│   ├── math3d.py        # 向量数学 + 颜色工具
│   ├── constants.py     # 常量
│   ├── camera.py        # 相机
│   ├── renderer.py      # 渲染辅助 + 粒子系统
│   └── game.py          # 游戏逻辑 + 渲染循环
├── .github/workflows/
│   └── build.yml        # CI: 测试 → Pages 部署 / exe 构建 → Release
├── pyproject.toml
└── README.md
```

## CI/CD

| 触发条件 | 动作 |
|---------|------|
| push 到 main | 运行测试 → 部署 GitHub Pages 网站 |
| push tag `v*` | 运行测试 → 构建 Windows exe → 发布 GitHub Release |

## 特性

- 10x10x10 三维空间，六方向移动
- 软件渲染 3D 管线（无 OpenGL/Three.js，纯 Canvas 2D 手写渲染）
- lookAt 相机 + 透视投影 + 画家算法深度排序 + 背面剔除 + Lambert 光照
- 蛇身头尾渐变着色
- 平滑插值移动
- 吃食物粒子爆发 + 屏幕震动
- 摄像机自动旋转 + 手动控制
- 食物脉动动画
- 穿墙 / 撞墙双模式
- 暂停 / 游戏结束 / 胜利界面
- Web 版支持触屏控制
