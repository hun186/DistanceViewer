import sys
import subprocess

# 檢查是否在 Google Colab 中運行
if 'google.colab' in sys.modules:
    subprocess.check_call(['pip', 'install', 'ipympl'])
    # 啟用 widget 後端
    get_ipython().run_line_magic('matplotlib', 'widget')

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Delaunay
from matplotlib.widgets import TextBox, Button, RadioButtons
import json
import os

# 檢查和設置字型
font_name = 'DFKai-SB'  # 標楷體

import matplotlib.font_manager as fm
if font_name not in [f.name for f in fm.fontManager.ttflist]:
    print(f"字型 {font_name} 不可用，將使用預設字型並切換至英文顯示。")
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # 使用 matplotlib 預設的 sans-serif 字型
    plt.rcParams['axes.unicode_minus'] = False  # 確保負號正常顯示
    use_chinese = False  # 是否使用中文
    x_label = "X Coordinate"
    y_label = "Y Coordinate"
    title = "Interactive Point Management"
else:
    plt.rcParams['font.sans-serif'] = [font_name]  # 使用標楷體
    plt.rcParams['axes.unicode_minus'] = False  # 確保負號正常顯示
    use_chinese = True  # 使用中文
    x_label = "X座標"
    y_label = "Y座標"
    title = "互動式點管理"

class InteractivePlot:
    def __init__(self, drag_threshold=5, select_threshold=2.0, save_file="points.json"):
        self.fig, self.ax = plt.subplots()
        self.points = []
        self.colors = []  # 保存每个点的颜色
        self.current_color = 'blue'  # 默认颜色
        self.history = []  # 用于记录历史状态的栈
        self.selected_point_index = None
        self.cursor_text = self.ax.text(0, 0, '', fontsize=12, color='green', zorder=6)  # 游標位置顯示文本
        self.press = None  # 用于记录鼠标拖动的起始点
        self.drag_threshold = drag_threshold  # 拖动的距离阈值
        self.select_threshold = select_threshold  # 选择拖动点的距离阈值
        self.dragging = False  # 用于判断是否在拖动
        self.save_file = save_file  # 保存点的文件路径
        self.action_log = []  # 动作记录

        # 增加文本框，移到畫面右側
        self.text_box_label_ax = self.fig.add_axes([0.75, 0.7, 0.2, 0.05])
        self.text_box_label_ax.axis("off")
        if use_chinese:
            self.text_box_label_ax.text(0.5, 0.5, "輸入座標 (x, y):", ha="center", va="center", fontsize=12)
        else:
            self.text_box_label_ax.text(0.5, 0.5, "Input coordinates (x, y):", ha="center", va="center", fontsize=12)

        self.text_box_ax = self.fig.add_axes([0.75, 0.64, 0.2, 0.05])
        self.text_box = TextBox(self.text_box_ax, '', initial="")
        self.text_box.on_submit(self.submit)

        # 保存按钮
        self.save_button_ax = self.fig.add_axes([0.75, 0.56, 0.09, 0.05])
        self.save_button = Button(self.save_button_ax, '保存' if use_chinese else 'Save')
        self.save_button.on_clicked(self.save_points)

        # 载入按钮
        self.load_button_ax = self.fig.add_axes([0.86, 0.56, 0.09, 0.05])
        self.load_button = Button(self.load_button_ax, '載入' if use_chinese else 'Load')
        self.load_button.on_clicked(self.load_points)

        # 颜色选择器
        self.color_ax = self.fig.add_axes([0.75, 0.4, 0.2, 0.15])
        self.color_buttons = RadioButtons(self.color_ax, ('blue', 'red', 'green', 'orange', 'purple'))
        self.color_buttons.on_clicked(self.change_color)

        # 使用說明
        self.instructions_ax = self.fig.add_axes([0.75, 0.05, 0.2, 0.3])  # 調整位置，將說明框向下移動
        self.instructions_ax.axis("off")
        if use_chinese:
            instructions_text = (
                "使用說明:\n"
                "- 左鍵點擊: 新增點或更改顏色\n"
                "- 右鍵點擊: 移除點\n"
                "- 拖動: 移動點\n"
                "- 座標格式: x, y\n"
                "- 保存: 保存目前座標\n"
                "- 載入: 載入先前座標\n"
                "- 顏色: 選擇新增或變更點的顏色\n"
            )
        else:
            instructions_text = (
                "Instructions:\n"
                "- Left Click: Add or Change Color\n"
                "- Right Click: Remove Point\n"
                "- Drag: Move Point\n"
                "- Coord Format: x, y\n"
                "- Save: Save Current Points\n"
                "- Load: Load Previous Points\n"
                "- Color: Select or Change Point Color\n"
            )
        self.instructions_ax.text(0, 1, instructions_text, ha="left", va="top", fontsize=10)

        # 动作说明对话框
        self.action_log_ax = self.fig.add_axes([0.75, 0.8, 0.2, 0.18])  # 置于右上角
        self.action_log_ax.axis("off")
        self.action_log_text = self.action_log_ax.text(0, 1, "", ha="left", va="top", fontsize=10)

        # 连接事件处理程序
        self.cid_press = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.cid_release = self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_key = self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(100, 0)  # 反轉 y 軸，將 (0,0) 設置在左上角
        self.ax.set_aspect('equal', 'box')  # 設置坐標軸比例為1:1
        self.ax.grid(True, zorder=1)  # 确保网格位于下层

        # 調整x軸顯示在上方
        self.ax.xaxis.set_label_position('top')
        self.ax.xaxis.tick_top()

        plt.subplots_adjust(right=0.72)  # 調整子圖佈局，給文本框留出空間

        # 移動標題與軸標籤到座標圖附近
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)

    def log_action(self, action):
        """記錄並顯示執行的操作"""
        self.action_log.append(action)
        if len(self.action_log) > 10:
            self.action_log.pop(0)
        self.action_log_text.set_text("\n".join(self.action_log))
        self.fig.canvas.draw_idle()

    def change_color(self, label):
        """更改当前颜色，并将其应用于选定的点或下一个新点"""
        self.current_color = label  # 更改当前颜色，供下次新增点使用
        if self.selected_point_index is not None:
            self.colors[self.selected_point_index] = label
            self.redraw()
            self.log_action(f"更改點顏色: {label}")
        else:
            self.log_action(f"顏色選擇: {label}")

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        x, y = round(event.xdata), round(event.ydata)

        if not (0 <= x <= 100 and 0 <= y <= 100):
            return

        if event.button == 1:  # 左鍵選取或新增點
            for i, point in enumerate(self.points):
                if self.distance(point, (x, y)) < self.select_threshold:
                    self.selected_point_index = i
                    self.press = (x, y)
                    self.dragging = False
                    self.log_action(f"選擇點: ({point[0]}, {point[1]})")
                    return

            # 如果没有选中点，则准备添加新点
            self.press = (x, y)
            self.selected_point_index = None  # 重置選擇點
            self.dragging = False

        elif event.button == 3:  # 右鍵刪除點
            for i, point in enumerate(self.points):
                if self.distance(point, (x, y)) < self.select_threshold:
                    self.save_history()  # 保存当前状态到历史记录
                    self.points.pop(i)
                    self.colors.pop(i)  # 同時移除相應的顏色
                    self.redraw()
                    self.log_action(f"移除點: ({point[0]}, {point[1]})")
                    return

    def on_release(self, event):
        if self.press is None:  # 如果 self.press 是 None，直接返回
            return

        if self.selected_point_index is None and not self.dragging:  # 如果没有拖动且没有选中点，添加新点
            x, y = self.press
            if (x, y) != (0, 0):  # 确保不会添加错误的 (0, 0) 点
                self.save_history()  # 保存当前状态到历史记录
                self.points.append((x, y))
                self.colors.append(self.current_color)  # 保存点的颜色
                self.redraw()
                self.log_action(f"新增點: ({x}, {y})")
                self.selected_point_index = None  # 添加新点后重置索引
        elif self.dragging:
            if self.selected_point_index is not None:
                x, y = round(event.xdata), round(event.ydata)
                self.points[self.selected_point_index] = (x, y)
                self.redraw()
                self.log_action(f"移動點至: ({x}, {y})")

        self.press = None  # 结束拖动
        self.dragging = False

    def on_motion(self, event):
        """更新鼠标移动时的显示"""
        if event.inaxes != self.ax:
            return

        x, y = round(event.xdata), round(event.ydata)
        # 更新游標位置的顯示
        self.cursor_text.set_position((x + 2, y))
        self.cursor_text.set_text(f'({x}, {y})')

        if self.press is not None and self.selected_point_index is not None:  # 如果正在拖动
            if self.distance(self.press, (x, y)) > self.drag_threshold:
                self.dragging = True
                if 0 <= x <= 100 and 0 <= y <= 100:
                    self.points[self.selected_point_index] = (x, y)
                    self.redraw()

        self.fig.canvas.draw_idle()

    def on_key_press(self, event):
        if event.key == 'ctrl+z':
            self.undo()

    def submit(self, text):
        try:
            x_str, y_str = text.split(',')
            x, y = int(x_str), int(y_str)
            if 0 <= x <= 100 and 0 <= y <= 100:
                self.save_history()  # 保存当前状态到历史记录
                self.points.append((x, y))
                self.colors.append(self.current_color)  # 保存点的颜色
                self.redraw()
                self.log_action(f"輸入點: ({x}, {y})")
            else:
                print("座標範圍應該在 (0, 0) 到 (100, 100) 之間" if use_chinese else "Coordinates should be between (0, 0) and (100, 100)")
        except ValueError:
            print("請輸入有效的座標，如 '10, 20'" if use_chinese else "Please enter valid coordinates, e.g., '10, 20'")

        self.text_box.set_val('')  # 重置文本框內容

    def save_history(self):
        """保存当前状态到历史记录"""
        self.history.append((self.points.copy(), self.colors.copy()))  # 保存points和colors的当前状态

    def undo(self):
        """撤销上一步操作"""
        if self.history:
            self.points, self.colors = self.history.pop()  # 恢复上一步状态
            self.redraw()
            self.log_action("撤銷上一步")

    def save_points(self, event=None):
        """保存当前点到文件"""
        data = {'points': self.points, 'colors': self.colors}
        with open(self.save_file, 'w') as f:
            json.dump(data, f)
        self.log_action(f"已保存到 {self.save_file}")

    def load_points(self, event=None):
        """从文件载入点"""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r') as f:
                    data = json.load(f)
                # 验证数据格式是否正确
                if ('points' in data and isinstance(data['points'], list) and 
                    all(isinstance(p, list) and len(p) == 2 for p in data['points']) and
                    'colors' in data and isinstance(data['colors'], list) and 
                    len(data['points']) == len(data['colors'])):
                    self.points = data['points']
                    self.colors = data['colors']
                    self.redraw()
                    self.log_action(f"已從 {self.save_file} 载入資料")
                else:
                    print(f"檔案格式錯誤: {self.save_file}" if use_chinese else f"File format error: {self.save_file}")
            except json.JSONDecodeError:
                print(f"無法解析 JSON 文件: {self.save_file}" if use_chinese else f"Cannot parse JSON file: {self.save_file}")
        else:
            print(f"{self.save_file} 不存在" if use_chinese else f"{self.save_file} does not exist")

    def distance(self, point1, point2):
        return np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def intersect(self, p1, p2, q1, q2):
        """检查两条线段是否相交"""
        def ccw(A, B, C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
        return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)

    def redraw(self):
        self.ax.clear()
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(100, 0)  # 保持y軸反轉
        self.ax.set_aspect('equal', 'box')  # 設置坐標軸比例為1:1
        self.ax.grid(True, zorder=1)  # 确保网格位于下层
        # 保持x軸顯示在上方
        self.ax.xaxis.set_label_position('top')
        self.ax.xaxis.tick_top()
    
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(title)
    
        for point, color in zip(self.points, self.colors):
            self.ax.scatter(*point, color=color, zorder=3)  # 确保点位于上层
            # 在每個點的旁邊顯示其座標值
            self.ax.text(point[0] + 1, point[1] - 1, f'({point[0]}, {point[1]})', fontsize=10, color=color, zorder=4)
    
        # 使用 Delaunay 三角化
        if len(self.points) >= 3:
            points_array = np.array(self.points)
            tri = Delaunay(points_array)

            for simplex in tri.simplices:
                pts = points_array[simplex]
                angles = self.calculate_angles(pts)
                if all(angle <= 160 for angle in angles):  # 检查角度是否小于160度
                    self.draw_triangle(pts)

        self.fig.canvas.draw()

    def calculate_angles(self, pts):
        """计算三角形三个内角的角度"""
        a = np.linalg.norm(pts[1] - pts[0])
        b = np.linalg.norm(pts[2] - pts[1])
        c = np.linalg.norm(pts[0] - pts[2])
        angleA = np.degrees(np.arccos((b**2 + c**2 - a**2) / (2 * b * c)))
        angleB = np.degrees(np.arccos((a**2 + c**2 - b**2) / (2 * a * c)))
        angleC = np.degrees(np.arccos((a**2 + b**2 - c**2) / (2 * a * b)))
        return [angleA, angleB, angleC]

    def draw_triangle(self, pts):
        """绘制三角形"""
        triangle = plt.Polygon(pts, edgecolor='black', fill=None, lw=2, zorder=2)
        self.ax.add_patch(triangle)

        # 绘制边的距离信息，并避免与点或边重叠
        for i in range(3):
            p1 = pts[i]
            p2 = pts[(i + 1) % 3]
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            distance = self.distance(p1, p2)
            self.ax.text(mid_x, mid_y, f'{distance:.2f}', fontsize=10, color='gray', zorder=5)

if __name__ == "__main__":
    plot = InteractivePlot()  # 不限制邻近点数量
    plt.show()
