import math
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from QCustomPlot_PyQt5 import QCustomPlot, QCP

class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 1. 创建 QCustomPlot 对象
        self.custom_plot = QCustomPlot(self)

        # 2. 配置交互功能 (核心部分)
        self.setup_interactions()

        # 3. 绘制初始曲线
        self.add_sine_curve()

        # 2. 创建布局并将 custom_plot 添加进去
        layout = QVBoxLayout()
        layout.addWidget(self.custom_plot)
        layout.setContentsMargins(0, 0, 0, 0)  # 去掉边距，让图表贴边
        self.setLayout(layout)

    def setup_interactions(self):
        """
        配置图表的鼠标交互行为
        """
        # 启用鼠标拖拽(iRangeDrag)和滚轮缩放(iRangeZoom)
        self.custom_plot.setInteractions(QCP.iRangeDrag | QCP.iRangeZoom)

        # 设置拖拽和缩放的方向为水平和垂直
        self.custom_plot.axisRect().setRangeDrag(Qt.Horizontal | Qt.Vertical)
        self.custom_plot.axisRect().setRangeZoom(Qt.Horizontal | Qt.Vertical)

    def add_sine_curve(self):
        """添加一条正弦曲线"""
        graph = self.custom_plot.addGraph()
        graph.setPen(QPen(Qt.blue, 2))  # 蓝色，线宽2
        graph.setName("sin(x)")  # 图例名称

        # 生成数据
        x, y = [], []
        for i in range(500):
            x_val = i / 50.0
            x.append(x_val)
            y.append(math.sin(x_val))

        graph.setData(x, y)
        self.custom_plot.replot()

    def add_cos_curve(self):
        """添加一条余弦曲线"""
        graph = self.custom_plot.addGraph()
        graph.setPen(QPen(Qt.red, 2, Qt.DashLine))  # 红色，虚线
        graph.setName("cos(x)")

        # 生成数据
        x, y = [], []
        for i in range(500):
            x_val = i / 50.0
            x.append(x_val)
            y.append(math.cos(x_val))

        graph.setData(x, y)

        # 显示图例
        self.custom_plot.legend.setVisible(True)
        self.custom_plot.replot()

    def rescale_view(self):
        """将所有坐标轴范围调整为显示所有图形"""
        self.custom_plot.rescaleAxes()
        self.custom_plot.replot()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlotWindow()
    window.show()
    sys.exit(app.exec_())