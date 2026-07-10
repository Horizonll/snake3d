"""3D Snake — 纯 Python 标准库实现的 3D 贪吃蛇游戏。

自研软件 3D 渲染管线（透视投影 + 画家算法深度排序），
基于 tkinter Canvas 绘制，零外部依赖。

控制:
  W/S/A/D      前进/后退/左/右（相对摄像机方向）
  Space/Shift  上升/下降
  方向键       旋转摄像机视角
  R            重置摄像机
  F            切换相机跟随蛇头
  P            暂停/继续
  T            切换穿墙/撞墙模式
  Enter        重新开始（游戏结束后）
"""

from snake.game import Snake3DGame


def main():
    game = Snake3DGame()
    game.run()


if __name__ == "__main__":
    main()
