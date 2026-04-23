import math
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from QCustomPlot_PyQt5 import QCustomPlot, QCP

from mypackage.src.TraceData import TraceData

class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()

        #字典，对应C++:QMap<QString, QCPGraph*> graph_map;键为字符串、值为 QCPGraph 指针的映射表
        self.graph_dict = {}
        self.trace_dict = {}
        self.start_time_stamp = 0
        self.replot_wait = False

        self.replot_timer = QTimer()
        self.replot_timer.setInterval(30)
        self.replot_timer.setSingleShot(True)
        self.replot_timer.timeout.connect(self.do_replot)

        self.replot_text_timer = QTimer()
        self.replot_text_timer.setInterval(100)
        self.replot_text_timer.setSingleShot(True)
        self.replot_text_timer.timeout.connect(self.update_text_position)

        # 1. 创建 QCustomPlot 对象
        self.custom_plot = QCustomPlot(self)

        # 2. 配置交互功能 (核心部分)
        self.setup_interactions()

        # 3. 创建布局并将 custom_plot 添加进去
        layout = QVBoxLayout()
        layout.addWidget(self.custom_plot)
        layout.setContentsMargins(0, 0, 0, 0)  # 去掉边距，让图表贴边
        self.setLayout(layout)

    def replot(self):
        if self.replot_timer.isActive():
            self.replot_wait = True
            return
        self.custom_plot.replot()
        self.replot_timer.start()

    def do_replot(self):
        if self.replot_wait:
            self.custom_plot.replot()
            self.replot_wait = False

    def update_text_position(self):
        TraceData.adjust_position(list(self.trace_dict.values()))
        self.custom_plot.replot()

    def add_graph(self, name, color):
        graph = self.custom_plot.addGraph()
        graph.setPen(QPen(QColor(color), 2))  # 颜色，线宽
        graph.setName(str(name))  # 图例名称

        self.graph_dict[name] = graph  # 字典添加

        trace = TraceData(self.custom_plot, graph)
        self.trace_dict[name] = trace  # 字典添加

        self.set_graph_visible(name, True)

    def add_data(self, name, time_stamp, value):
        """重载函数：添加单点数据"""
        graph = self.graph_dict[name]
        if not graph: return

        if self.start_time_stamp == 0:
            self.start_time_stamp = time_stamp

        time = time_stamp - self.start_time_stamp
        graph.setData(time, value)

        if graph.visible():
            trace = self.trace_dict[name]
            trace.update()
            self.replot_text_timer.stop()
            self.replot_text_timer.start()

        self.replot()

    def setup_interactions(self):
        """
        配置图表的鼠标交互行为
        """
        # 启用鼠标拖拽(iRangeDrag)和滚轮缩放(iRangeZoom)
        self.custom_plot.setInteractions(QCP.iRangeDrag | QCP.iRangeZoom)

        # 设置拖拽和缩放的方向为水平和垂直
        self.custom_plot.axisRect().setRangeDrag(Qt.Horizontal | Qt.Vertical)
        self.custom_plot.axisRect().setRangeZoom(Qt.Horizontal | Qt.Vertical)

    def set_graph_visible(self, name, on):
        graph = self.graph_dict[name]
        trace = self.trace_dict[name]
        if not graph or not trace: return

        if on:
            # graph.setSelectable(QCP.stDataRange)
            # graph.addToLegend()
            graph.setSelectable(True)
            trace.set_visible(True)
            trace.update()
        else:
            graph.setSelectable(QCP.stNone)
            trace.SetVisable(False)
        graph.setVisible(True)
        self.custom_plot.legend.setVisible(self.custom_plot.legend.itemCount() > 0)
        self.replot()










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
    window = PlotWidget()
    window.show()
    sys.exit(app.exec_())