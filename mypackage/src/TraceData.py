from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QWidget
from QCustomPlot_PyQt5 import QCustomPlot, QCP, QCPGraph, QCPItemTracer, QCPItemText, QCPItemPosition


class TraceData(QWidget):
    def __init__(self, parent: QCustomPlot, graph: QCPGraph):
        super().__init__()

        self.qcustomplot = parent
        self.graph = graph
        self.visible = False
        self.key = 0.0
        self.value = 0.0

        # 创建 tracer（追踪点）
        self.tracer = QCPItemTracer(self.qcustomplot)
        self.tracer.setSelectable(False)
        self.tracer.setPen(graph.pen())
        self.tracer.setGraph(graph)
        self.tracer.setVisible(False)

        # 创建 label（标签文字）
        self.label = QCPItemText(self.qcustomplot)
        self.label.setSelectable(False)
        self.label.position.setParentAnchor(self.tracer.position, True)
        self.label.setVisible(False)
        self.label.position.setTypeY(QCPItemPosition.ptAbsolute)
        self.label.position.setCoords(20, 0)
        self.label.setText("")

        self.update()

    def __del__(self):
        # Python 没有手动 delete，但可以尝试移除 item
        self.qcustomplot.removeItem(self.tracer)
        self.qcustomplot.removeItem(self.label)

    def set_visible(self, visible: bool):
        self.visible = visible
        self.label.setVisible(visible)

    def get_visible(self) -> bool:
        return self.visible

    def set_key(self, axis: float):
        self.tracer.setGraphKey(axis)
        self.label.setText(str(self.tracer.position.value()))
        self.tracer.updatePosition()

    def set_pen(self, pen: QPen):
        self.label.setColor(pen.color())

    def get_value(self) -> float:
        return self.value

    def get_label(self) -> QCPItemText:
        return self.label

    def update(self):
        graph = self.tracer.graph()

        if graph.dataCount() > 0:
            # 获取最后一个数据点
            it = graph.data().end()
            it -= 1
            self.key = it.key
            self.value = it.value

            self.tracer.setGraphKey(self.key)
            self.tracer.updatePosition()
            self.label.setText(str(self.value))


def compare_by_value(a: TraceData, b: TraceData) -> bool:
    return a.get_value() < b.get_value()


def adjust_position(trace_list: list):
    """静态方法：调整所有可见 trace 的 label 位置，防止重叠"""
    traces = [t for t in trace_list if t.Visable()]

    # 按 value 排序
    traces.sort(key=lambda x: x.getValue())

    last_label = None
    for i, trace in enumerate(traces):
        curr_label = trace.getLabel()
        curr_label.position.setCoords(20, 0)

        if last_label is not None:
            # 如果当前 label 底部像素 y 坐标 > 上一个 label 顶部像素 y 坐标，说明重叠了
            if curr_label.bottom.pixelPosition().y() > last_label.top.pixelPosition().y():
                # 把当前 label 往上挪，放到上一个 label 上面一点
                new_y = last_label.position.pixelPosition().y() - 10
                curr_label.position.setPixelPosition(QPointF(curr_label.position.pixelPosition().x(), new_y))

        last_label = curr_label