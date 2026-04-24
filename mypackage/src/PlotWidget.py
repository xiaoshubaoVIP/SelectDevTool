import math
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from QCustomPlot_PyQt5 import QCustomPlot, QCP, QCPGraph

from mypackage.src.TraceData import TraceData, adjust_position


class MyCustomPlot(QCustomPlot):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. 开启交互总开关
        self.setInteractions(QCP.iRangeDrag | QCP.iRangeZoom)

        # 2. 设置默认拖拽和缩放方向
        self.axisRect().setRangeDrag(Qt.Horizontal | Qt.Vertical)
        self.axisRect().setRangeZoom(Qt.Horizontal)  # 默认为水平缩放

    def wheelEvent(self, event):
        """
        在这里拦截滚轮事件，根据 Ctrl 键动态修改缩放轴
        """
        # 1. 检查是否按住了 Ctrl 键
        if event.modifiers() & Qt.ControlModifier:
            # 按住 Ctrl：只缩放 Y 轴 (垂直)
            print("Ctrl 按下 -> 缩放 Y 轴")
            self.axisRect().setRangeZoom(Qt.Vertical)
        else:
            # 未按 Ctrl：只缩放 X 轴 (水平)
            print("Ctrl 未按下 -> 缩放 X 轴")
            self.axisRect().setRangeZoom(Qt.Horizontal)

        # 2. 调用父类 (QCustomPlot) 的 wheelEvent 执行实际缩放
        super().wheelEvent(event)

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
        # self.replot_text_timer.timeout.connect(self.update_text_position)

        # 1. 创建 QCustomPlot 对象
        self.custom_plot = MyCustomPlot()

        # 2. 创建布局并将 custom_plot 添加进去
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

    # def update_text_position(self):
    #     adjust_position(list(self.trace_dict.values()))
    #     self.replot()

    def add_graph(self, name, color):
        graph = self.custom_plot.addGraph()
        graph.setPen(QPen(QColor(color), 2))    # 颜色，线宽
        graph.setName(str(name))                # 图例名称，显示右上角

        self.graph_dict[name] = graph           # 字典添加graph

        trace = TraceData(self.custom_plot, graph)
        self.trace_dict[name] = trace           # 字典添加trace

        self.set_graph_visible(name, True)

    def add_data(self, name, time_stamp:int, value:int):
        """重载函数：添加单点数据"""
        graph = self.graph_dict[name]

        if not graph: return

        if self.start_time_stamp == 0:
            self.start_time_stamp = time_stamp

        time = time_stamp - self.start_time_stamp

        graph.addData(time, value)

        if graph.visible():
            trace = self.trace_dict[name]
            trace.update()
            self.replot_text_timer.stop()
            self.replot_text_timer.start()

        self.replot()

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


    def rescale_view(self):
        """将所有坐标轴范围调整为显示所有图形"""
        self.custom_plot.rescaleAxes()
        self.replot()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlotWidget()
    window.show()
    sys.exit(app.exec_())