import configparser
import math
import os
import re
import time
from bisect import bisect_left
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import serial
import serial.tools.list_ports
from PyQt5 import QtCore
from PyQt5.QtCore import QRectF, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen, QTextCursor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QCheckBox,
    QComboBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGraphicsRectItem,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

import pyqtgraph as pg
from openpyxl import Workbook

from mypackage.src.tester_protocol import (
    FrameParser,
    bytes_to_hex,
    extract_log_timestamp,
    extract_receive_hex,
    hex_to_bytes,
)


@dataclass
class GraphConfig:
    name: str
    offset: int
    length: int
    signed: bool
    color: str


@dataclass
class SeriesData:
    config: GraphConfig
    visible: bool = True
    current: int = 0
    maximum: Optional[int] = None
    minimum: Optional[int] = None
    timestamps: List[int] = field(default_factory=list)
    values: List[int] = field(default_factory=list)
    curve: Optional[pg.PlotDataItem] = None


@dataclass
class MarkData:
    name: str
    device_id: str
    start: int
    end: Optional[int] = None
    sensitivity: Optional[float] = None
    angle: str = ""
    start_line: Optional[pg.InfiniteLine] = None
    end_line: Optional[pg.InfiniteLine] = None
    region: Optional[pg.LinearRegionItem] = None
    label_text: Optional[pg.TextItem] = None
    label_base_x_span: float = 1.0
    label_base_y_span: float = 1.0


class AxisZoomViewBox(pg.ViewBox):
    selectionChanged = pyqtSignal(float, float, float, float, bool)

    def __init__(self) -> None:
        super().__init__()
        self.setMouseEnabled(x=True, y=False)

    def wheelEvent(self, ev, axis=None) -> None:
        zoom_y = bool(ev.modifiers() & Qt.ControlModifier)

        scale = 1.02 ** (ev.delta() * self.state["wheelScaleFactor"])
        center = self.mapSceneToView(ev.scenePos())
        self._resetTarget()
        if zoom_y:
            self.scaleBy(y=scale, center=center)
            self.sigRangeChangedManually.emit([False, True])
        else:
            self.scaleBy(x=scale, center=center)
            self.sigRangeChangedManually.emit([True, False])
        ev.accept()

    def mouseDragEvent(self, ev, axis=None) -> None:
        if ev.button() == Qt.LeftButton and not (ev.modifiers() & Qt.ControlModifier):
            start = self.mapSceneToView(ev.buttonDownScenePos())
            current = self.mapSceneToView(ev.scenePos())
            self.selectionChanged.emit(start.x(), current.x(), start.y(), current.y(), ev.isFinish())
            ev.accept()
            return
        super().mouseDragEvent(ev, axis=axis)


class AlignedPlotWidget(pg.PlotWidget):
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        self.draw_aligned_axes()

    def draw_aligned_axes(self) -> None:
        view_box = self.getViewBox()
        if view_box is None:
            return
        x_range, y_range = view_box.viewRange()
        scene_rect = view_box.sceneBoundingRect()
        if scene_rect.width() <= 0 or scene_rect.height() <= 0:
            return

        top_left = self.mapFromScene(scene_rect.topLeft())
        bottom_right = self.mapFromScene(scene_rect.bottomRight())
        left = float(top_left.x())
        top = float(top_left.y())
        right = float(bottom_right.x())
        bottom = float(bottom_right.y())

        painter = QPainter(self.viewport())
        try:
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            self.draw_y_axis(painter, view_box, x_range, y_range, left, top, right, bottom)
            self.draw_x_axis(painter, view_box, x_range, y_range, left, top, right, bottom)
        finally:
            painter.end()

    def draw_y_axis(self, painter, view_box, x_range, y_range, left, top, right, bottom) -> None:
        ticks = self.tick_values(y_range[0], y_range[1], 8)
        grid_pen = QPen(QColor(224, 224, 224), 1)
        axis_pen = QPen(QColor(150, 150, 150), 1)
        text_pen = QPen(QColor(115, 115, 115), 1)

        painter.setPen(grid_pen)
        for value in ticks:
            scene_pos = view_box.mapViewToScene(QtCore.QPointF(x_range[0], value))
            y = float(self.mapFromScene(scene_pos).y())
            if top <= y <= bottom:
                painter.drawLine(QtCore.QPointF(left, y), QtCore.QPointF(right, y))

        painter.setPen(axis_pen)
        painter.drawLine(QtCore.QPointF(left, top), QtCore.QPointF(left, bottom))

        painter.setPen(text_pen)
        for value in ticks:
            scene_pos = view_box.mapViewToScene(QtCore.QPointF(x_range[0], value))
            y = float(self.mapFromScene(scene_pos).y())
            if top <= y <= bottom:
                painter.drawText(
                    QtCore.QRectF(left - 54, y - 9, 48, 18),
                    Qt.AlignRight | Qt.AlignVCenter,
                    self.format_tick(value),
                )

        painter.save()
        painter.translate(left - 50, (top + bottom) / 2)
        painter.rotate(-90)
        painter.drawText(QtCore.QRectF(-40, -10, 80, 20), Qt.AlignCenter, "数值")
        painter.restore()

    def draw_x_axis(self, painter, view_box, x_range, y_range, left, top, right, bottom) -> None:
        ticks = self.tick_values(x_range[0], x_range[1], 8)
        grid_pen = QPen(QColor(224, 224, 224), 1)
        axis_pen = QPen(QColor(150, 150, 150), 1)
        text_pen = QPen(QColor(115, 115, 115), 1)

        painter.setPen(grid_pen)
        for value in ticks:
            scene_pos = view_box.mapViewToScene(QtCore.QPointF(value, y_range[0]))
            x = float(self.mapFromScene(scene_pos).x())
            if left <= x <= right:
                painter.drawLine(QtCore.QPointF(x, top), QtCore.QPointF(x, bottom))

        painter.setPen(axis_pen)
        painter.drawLine(QtCore.QPointF(left, bottom), QtCore.QPointF(right, bottom))

        painter.setPen(text_pen)
        for value in ticks:
            scene_pos = view_box.mapViewToScene(QtCore.QPointF(value, y_range[0]))
            x = float(self.mapFromScene(scene_pos).x())
            if left <= x <= right:
                painter.drawText(
                    QtCore.QRectF(x - 28, bottom + 2, 56, 18),
                    Qt.AlignHCenter | Qt.AlignTop,
                    self.format_tick(value),
                )
        painter.drawText(QtCore.QRectF(left, bottom + 24, right - left, 18), Qt.AlignCenter, "时间 (s)")

    @classmethod
    def tick_values(cls, lower: float, upper: float, count: int) -> List[float]:
        if lower > upper:
            lower, upper = upper, lower
        span = upper - lower
        if span <= 0:
            return [lower]
        step = cls.nice_tick_step(span / max(count, 1))
        start = math.ceil(lower / step) * step
        ticks = []
        value = start
        limit = upper + step * 0.5
        while value <= limit:
            ticks.append(value)
            value += step
        return ticks

    @staticmethod
    def nice_tick_step(value: float) -> float:
        if value <= 0:
            return 1
        exponent = math.floor(math.log10(value))
        fraction = value / (10 ** exponent)
        if fraction <= 1:
            nice_fraction = 1
        elif fraction <= 2:
            nice_fraction = 2
        elif fraction <= 5:
            nice_fraction = 5
        else:
            nice_fraction = 10
        return nice_fraction * (10 ** exponent)

    @staticmethod
    def format_tick(value: float) -> str:
        if abs(value) < 1e-9:
            value = 0
        if abs(value) >= 100 or abs(value - round(value)) < 1e-9:
            return f"{value:.0f}"
        return f"{value:g}"


class GraphConfigDialog(QDialog):
    def __init__(self, parent=None, config: Optional[GraphConfig] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("编辑曲线" if config else "添加曲线")
        self.color = config.color if config else "#000000"

        self.name_edit = QLineEdit(config.name if config else "")
        self.offset_edit = QLineEdit(str(config.offset) if config else "0")
        self.length_box = QComboBox()
        self.length_box.addItems(["1", "2", "4"])
        if config:
            self.length_box.setCurrentText(str(config.length))

        self.type_box = QComboBox()
        self.type_box.addItems(["signed", "unsigned"])
        if config:
            self.type_box.setCurrentText("signed" if config.signed else "unsigned")

        self.color_button = QPushButton(self.color)
        self.color_button.setStyleSheet(f"background-color: {self.color};")
        self.color_button.clicked.connect(self.pick_color)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("名称", self.name_edit)
        layout.addRow("偏移", self.offset_edit)
        layout.addRow("数据长度", self.length_box)
        layout.addRow("整形类型", self.type_box)
        layout.addRow("颜色", self.color_button)
        layout.addRow(buttons)

    def pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.color), self)
        if color.isValid():
            self.color = color.name()
            self.color_button.setText(self.color)
            self.color_button.setStyleSheet(f"background-color: {self.color};")

    def get_config(self) -> GraphConfig:
        return GraphConfig(
            name=self.name_edit.text().strip(),
            offset=int(self.offset_edit.text().strip()),
            length=int(self.length_box.currentText()),
            signed=self.type_box.currentText() == "signed",
            color=self.color,
        )

    def accept(self) -> None:
        try:
            cfg = self.get_config()
        except ValueError:
            QMessageBox.warning(self, "参数错误", "偏移必须是整数")
            return
        if not cfg.name:
            QMessageBox.warning(self, "参数错误", "名称不能为空")
            return
        super().accept()


class SerialReader(QThread):
    data_received = pyqtSignal(bytes)
    state_changed = pyqtSignal(bool, str)

    def __init__(self, params: Dict[str, object]) -> None:
        super().__init__()
        self.params = params
        self.running = False
        self.serial_port: Optional[serial.Serial] = None

    def run(self) -> None:
        try:
            self.serial_port = serial.Serial(timeout=0.2, **self.params)
            self.running = True
            self.state_changed.emit(True, "串口打开成功")
            while self.running:
                data = self.serial_port.read(self.serial_port.in_waiting or 1)
                if data:
                    self.data_received.emit(data)
        except Exception as exc:
            self.state_changed.emit(False, f"串口打开失败: {exc}")
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.running = False

    def stop(self) -> None:
        self.running = False
        self.wait(1500)

    def send(self, text: str) -> None:
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(text.encode("utf-8"))


class IntegratedTester(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.root = Path(QtCore.QDir.currentPath())
        self.setting_dir = self.root / "setting"
        self.output_dir = self.root / "output"
        self.log_dir = self.root / "log"
        self.setting_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

        self.parser = FrameParser()
        self.serial_thread: Optional[SerialReader] = None
        self.log_file_handle = None
        self.start_timestamp: Optional[int] = None
        self.series: Dict[str, SeriesData] = {}
        self.marks: List[MarkData] = []
        self.current_mark: Optional[MarkData] = None
        self._rescaling_y_axis = False
        self.mark_label_base_x_span = 1.0
        self.mark_label_base_y_span = 1.0
        self.mark_label_base_initialized = False
        self.cursor_x: Optional[float] = None
        self.smoke_status_text = ["正常", "校准", "通道1故障", "通道2故障", "水蒸气故障", "EMC故障", "预报", "报警", "静音"]
        self.smoke_type_text = [
            "无",
            "其他",
            "木头燃烧测试",
            "木头阴燃测试",
            "厨房油烟测试",
            "报纸燃烧测试",
            "聚氨酯燃烧测试",
            "聚氨酯阴燃测试",
            "厨房油烟和聚氨酯混合测试",
            "UL灵敏度测试",
            "EN灵敏度测试",
            "水蒸气",
        ]

        self._build_ui()
        self.load_graph_configs()
        self.refresh_ports()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        uart_layout = QHBoxLayout()
        mark_layout = QHBoxLayout()

        self.open_button = QPushButton("打开串口")
        self.open_button.clicked.connect(self.toggle_serial)
        self.port_box = QComboBox()
        self.baud_box = QComboBox()
        self.baud_box.addItems(["4800", "9600", "19200", "115200"])
        self.save_check = QCheckBox("保存数据")
        self.save_check.stateChanged.connect(self.toggle_raw_log)

        self.mark_type = QComboBox()
        self.mark_type.addItems(["UL烟雾", "PU烟雾", "油烟", "混合烟"])
        self.mark_id = QLineEdit()
        self.mark_id.setPlaceholderText("设备号")
        self.mark_note = QLineEdit()
        self.mark_note.setPlaceholderText("备注")
        self.angle_box = QComboBox()
        self.angle_box.addItems(["Null", "0", "45", "90", "135", "180"])
        self.mark_button = QPushButton("标记起点")
        self.mark_button.clicked.connect(self.toggle_mark)
        self.locate_button = QPushButton("定位")
        self.locate_button.clicked.connect(self.locate_mark)

        for widget in [
            self.open_button,
            self.port_box,
            self.baud_box,
            self.save_check,
        ]:
            uart_layout.addWidget(widget)
        uart_layout.addStretch(1)

        for widget in [
            QLabel("标记"),
            self.mark_type,
            QLabel("设备号"),
            self.mark_id,
            QLabel("备注"),
            self.mark_note,
            QLabel("角度"),
            self.angle_box,
            self.mark_button,
            self.locate_button,
        ]:
            mark_layout.addWidget(widget)
        mark_layout.addStretch(1)

        device_group = QGroupBox("Device")
        device_layout = QGridLayout(device_group)
        self.device_fault_label = QLabel("无")
        self.device_battery_label = QLabel("0")
        self.device_temp_label = QLabel("0")
        device_layout.addWidget(QLabel("故障:"), 0, 0)
        device_layout.addWidget(self.device_fault_label, 0, 1)
        device_layout.addWidget(QLabel("电池电量:"), 0, 2)
        device_layout.addWidget(self.device_battery_label, 0, 3)
        device_layout.addWidget(QLabel("温度:"), 0, 4)
        device_layout.addWidget(self.device_temp_label, 0, 5)

        sensor_group = QGroupBox("Sensor")
        sensor_layout = QGridLayout(sensor_group)
        self.smoke_state_label = QLabel("无")
        self.smoke_type_label = QLabel("无")
        self.smoke_state_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.smoke_type_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        sensor_layout.addWidget(QLabel("smoke状态:"), 0, 0)
        sensor_layout.addWidget(self.smoke_state_label, 0, 1)
        sensor_layout.addWidget(QLabel("smoke颗粒类型:"), 0, 2)
        sensor_layout.addWidget(self.smoke_type_label, 0, 3)

        info_layout = QVBoxLayout()
        info_layout.addWidget(device_group)
        info_layout.addWidget(sensor_group)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["名称", "当前值", "最大值", "最小值"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table.itemChanged.connect(self.table_item_changed)

        self.protocol_browser = QTextBrowser()
        self.protocol_browser.document().setMaximumBlockCount(1500)
        self.serial_browser = QTextBrowser()
        self.serial_browser.document().setMaximumBlockCount(1500)
        self.text_tabs = QTabWidget()
        self.text_tabs.addTab(self.protocol_browser, "协议")
        self.text_tabs.addTab(self.serial_browser, "串口")
        self.send_edit = QLineEdit()
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_serial_data)
        send_layout = QHBoxLayout()
        send_layout.addWidget(self.send_edit)
        send_layout.addWidget(self.send_button)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addLayout(uart_layout)
        left_layout.addLayout(info_layout)
        left_layout.addLayout(mark_layout)
        left_layout.addWidget(self.table, 3)
        left_layout.addWidget(self.text_tabs, 2)
        left_layout.addLayout(send_layout)

        self.plot_view = AxisZoomViewBox()
        self.plot_view.selectionChanged.connect(self.handle_plot_selection)
        self.plot = AlignedPlotWidget(viewBox=self.plot_view)
        self.plot.setBackground("w")
        self.plot.getPlotItem().getViewBox().setBackgroundColor("w")
        self.legend = self.plot.addLegend()
        self.position_plot_legend()
        self.plot.showGrid(x=False, y=False)
        self.plot.getViewBox().sigRangeChanged.connect(self.on_plot_range_changed)
        self.plot.setLabel("bottom", "")
        self.plot.setLabel("left", "")
        self.plot.getAxis("left").setWidth(58)
        self.plot.getAxis("bottom").setHeight(42)
        self.plot.getAxis("left").setStyle(showValues=False, tickLength=0)
        self.plot.getAxis("bottom").setStyle(showValues=False, tickLength=0)
        self.plot.getAxis("left").enableAutoSIPrefix(False)
        self.plot.getViewBox().enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
        self.plot.scene().sigMouseMoved.connect(self.handle_plot_mouse_moved)
        self.update_y_axis_ticks()

        self.setup_selection_items()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self.plot)
        splitter.setSizes([520, 1100])

        main_layout.addWidget(splitter)

    def setup_selection_items(self) -> None:
        self.selection_region = QGraphicsRectItem()
        self.selection_region.setPen(QPen(Qt.NoPen))
        self.selection_region.setBrush(QBrush(QColor(120, 120, 120, 18)))
        self.selection_region.setZValue(2)
        self.selection_region.setVisible(False)
        self.plot.addItem(self.selection_region, ignoreBounds=True)
        self.selection_region_edges = []
        selection_edge_pen = pg.mkPen("#888888", width=1, style=Qt.DashLine)
        for _ in range(4):
            edge = pg.PlotDataItem([], [], pen=selection_edge_pen, antialias=False, clipToView=False)
            edge.setZValue(3)
            edge.setVisible(False)
            self.plot.addItem(edge, ignoreBounds=True)
            self.selection_region_edges.append(edge)

        highlight_color = QColor("#1677ff")
        self.selection_highlight = pg.PlotDataItem(
            [],
            [],
            pen=pg.mkPen(highlight_color, width=1),
            symbol="o",
            symbolSize=3,
            symbolPen=pg.mkPen(highlight_color, width=1),
            symbolBrush=pg.mkBrush(highlight_color),
            pxMode=True,
            antialias=True,
            autoDownsample=False,
            clipToView=False,
        )
        self.selection_highlight.setDynamicRangeLimit(None)
        self.selection_highlight.setZValue(20)
        self.selection_highlight.setVisible(False)
        self.plot.addItem(self.selection_highlight, ignoreBounds=True)

        self.selection_text = pg.TextItem(anchor=(1, 0), border=pg.mkPen("#00aa44"), fill=(255, 255, 255, 235))
        self.selection_text.setZValue(30)
        self.selection_text.setVisible(False)
        self.plot.addItem(self.selection_text, ignoreBounds=True)
        self.update_selection_text_position()

        self.cursor_line = pg.InfiniteLine(pos=0, angle=90, movable=False)
        self.cursor_line.setPen(pg.mkPen("#111111", width=1, style=Qt.DotLine))
        self.cursor_line.setZValue(26)
        self.cursor_line.setVisible(False)
        self.plot.addItem(self.cursor_line, ignoreBounds=True)

        self.cursor_text = pg.TextItem(anchor=(0.5, 0), color=QColor("#111111"))
        self.cursor_text.setZValue(31)
        self.cursor_text.setVisible(False)
        self.plot.addItem(self.cursor_text, ignoreBounds=True)

    def update_selection_text_position(self, *args) -> None:
        if not hasattr(self, "selection_text"):
            return
        x_range, y_range = self.plot.getViewBox().viewRange()
        self.selection_text.setPos(x_range[1], y_range[1])

    def on_plot_range_changed(self, *args) -> None:
        self.update_selection_text_position()
        self.update_cursor_text_position()
        self.update_mark_label_positions()
        self.update_y_axis_ticks()

    def update_y_axis_ticks(self) -> None:
        if not hasattr(self, "plot"):
            return
        self.plot.viewport().update()

    def handle_plot_selection(
        self,
        start_x: float,
        end_x: float,
        start_y: float,
        cursor_y: float,
        finished: bool,
    ) -> None:
        left, right = sorted((start_x, end_x))
        if abs(right - left) <= 1e-9:
            return
        self.update_selection_region(left, right, start_y, cursor_y)
        if finished:
            self.update_selection_stats(left, right, cursor_y)
            self.set_selection_region_visible(False)

    def update_selection_region(self, left: float, right: float, start_y: float, end_y: float) -> None:
        if not hasattr(self, "selection_region"):
            return
        bottom, top = sorted((start_y, end_y))
        if abs(top - bottom) <= 1e-9:
            _, y_range = self.plot.getViewBox().viewRange()
            min_height = max(abs(y_range[1] - y_range[0]) * 0.06, 1)
            bottom = end_y - min_height / 2
            top = end_y + min_height / 2
        self.selection_region.setRect(QRectF(left, bottom, right - left, top - bottom))
        edge_data = [
            ([left, right], [top, top]),
            ([left, right], [bottom, bottom]),
            ([left, left], [bottom, top]),
            ([right, right], [bottom, top]),
        ]
        for edge, (x_values, y_values) in zip(self.selection_region_edges, edge_data):
            edge.setData(x_values, y_values)
        self.set_selection_region_visible(True)

    def set_selection_region_visible(self, visible: bool) -> None:
        if hasattr(self, "selection_region"):
            self.selection_region.setVisible(visible)
        for edge in getattr(self, "selection_region_edges", []):
            edge.setVisible(visible)

    def update_selection_stats(self, left: float, right: float, cursor_y: float) -> None:
        if self.start_timestamp is None:
            return
        self.rescale_y_axis_to_visible_data()

        best_item = None
        best_points = []
        best_distance = None
        for item in self.series.values():
            if not item.visible:
                continue
            points = [
                (ts - self.start_timestamp, value)
                for ts, value in zip(item.timestamps, item.values)
                if left <= ts - self.start_timestamp <= right
            ]
            if not points:
                continue
            distance = min(abs(value - cursor_y) for _, value in points)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_item = item
                best_points = points

        if not best_item or not best_points:
            self.selection_highlight.setData([], [])
            self.selection_highlight.setVisible(False)
            self.selection_text.setVisible(False)
            self.set_selection_region_visible(False)
            return

        x_values = [point[0] for point in best_points]
        y_values = [point[1] for point in best_points]
        count = len(y_values)
        max_value = max(y_values)
        min_value = min(y_values)
        mean_value = sum(y_values) / count
        duration = max(x_values) - min(x_values) if count > 1 else 0

        self.selection_highlight.setData(x_values, y_values)
        self.selection_highlight.setVisible(True)
        self.selection_text.setHtml(
            f"<span style='font-size:10pt;color:#000;'>"
            f"名称:{best_item.config.name}&nbsp;&nbsp;"
            f"数量:{count}&nbsp;&nbsp;"
            f"时间:{self.format_duration(duration)}&nbsp;&nbsp;"
            f"最大值:{max_value:g}&nbsp;&nbsp;"
            f"最小值:{min_value:g}&nbsp;&nbsp;"
            f"均值:{mean_value:.2f}"
            f"</span>"
        )
        self.selection_text.setVisible(True)
        self.update_selection_text_position()

    def handle_plot_mouse_moved(self, scene_pos) -> None:
        if not hasattr(self, "cursor_line"):
            return
        view_box = self.plot.getViewBox()
        if not view_box.sceneBoundingRect().contains(scene_pos):
            self.cursor_line.setVisible(False)
            self.cursor_text.setVisible(False)
            self.cursor_x = None
            return

        view_pos = view_box.mapSceneToView(scene_pos)
        x_range, y_range = view_box.viewRange()
        x_value, timestamp = self.nearest_visible_timestamp(view_pos.x(), x_range)
        if x_value is None:
            x_value = view_pos.x()
        if timestamp is None and self.start_timestamp is not None:
            timestamp = int(round(self.start_timestamp + x_value))
        self.cursor_x = x_value
        self.cursor_line.setPos(x_value)
        self.cursor_line.setVisible(True)
        self.cursor_text.setHtml(
            f"<span style='font-size:9pt;color:#111;'>{self.format_cursor_time(timestamp)}</span>"
        )
        self.cursor_text.setPos(x_value, self.cursor_label_y(y_range))
        self.cursor_text.setVisible(True)

    def update_cursor_text_position(self) -> None:
        if not hasattr(self, "cursor_text") or self.cursor_x is None:
            return
        _, y_range = self.plot.getViewBox().viewRange()
        self.cursor_text.setPos(self.cursor_x, self.cursor_label_y(y_range))

    @staticmethod
    def cursor_label_y(y_range: List[float]) -> float:
        return y_range[1] - (y_range[1] - y_range[0]) * 0.02

    def nearest_visible_timestamp(self, x_value: float, x_range: List[float]) -> tuple[Optional[float], Optional[int]]:
        if self.start_timestamp is None:
            return None, None
        target = self.start_timestamp + x_value
        best_x = None
        best_timestamp = None
        best_distance = None
        for item in self.series.values():
            if not item.visible or not item.timestamps:
                continue
            index = bisect_left(item.timestamps, target)
            for candidate_index in (index - 1, index):
                if candidate_index < 0 or candidate_index >= len(item.timestamps):
                    continue
                timestamp = item.timestamps[candidate_index]
                relative_x = timestamp - self.start_timestamp
                if relative_x < x_range[0] or relative_x > x_range[1]:
                    continue
                distance = abs(relative_x - x_value)
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_x = relative_x
                    best_timestamp = timestamp
        return best_x, best_timestamp

    @staticmethod
    def format_axis_number(value: float) -> str:
        if abs(value - round(value)) < 1e-9:
            return str(int(round(value)))
        return f"{value:.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def format_cursor_time(timestamp: Optional[int]) -> str:
        if timestamp is None:
            return "--"
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    @staticmethod
    def format_duration(seconds: float) -> str:
        total = int(round(seconds))
        mins, secs = divmod(total, 60)
        hours, mins = divmod(mins, 60)
        if hours:
            return f"{hours}h{mins}m{secs}s"
        if mins:
            return f"{mins}m{secs}s"
        return f"{secs}s"

    def load_graph_configs(self) -> None:
        previous_visible = {name: item.visible for name, item in self.series.items()}
        self.series.clear()
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.plot.clear()
        self.legend = self.plot.getPlotItem().legend or self.plot.addLegend()
        self.legend.clear()

        config_path = self.setting_dir / "table.ini"
        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")
        for section in config.sections():
            try:
                offset_text = config.get(section, "偏移", fallback="").strip()
                if not offset_text:
                    continue
                graph_config = GraphConfig(
                    name=section,
                    offset=int(offset_text),
                    length=int(config.get(section, "数据长度", fallback="1")),
                    signed=config.get(section, "整形类型", fallback="signed") == "signed",
                    color=config.get(section, "颜色", fallback="#000000") or "#000000",
                )
            except ValueError:
                continue

            curve = self.create_series_curve(graph_config)
            item = SeriesData(config=graph_config, curve=curve, visible=previous_visible.get(section, True))
            self.series[section] = item

            row = self.table.rowCount()
            self.table.insertRow(row)
            name_item = QTableWidgetItem(section)
            name_item.setCheckState(Qt.Checked if item.visible else Qt.Unchecked)
            self.table.setItem(row, 0, name_item)
            for col in range(1, 4):
                self.table.setItem(row, col, QTableWidgetItem("0"))

        self.refresh_series_visibility()
        self.setup_selection_items()
        self.table.blockSignals(False)

    def create_series_curve(self, graph_config: GraphConfig) -> pg.PlotDataItem:
        color = QColor(graph_config.color)
        curve = pg.PlotDataItem(
            [],
            [],
            pen=pg.mkPen(color, width=0.7),
            symbol="o",
            symbolSize=2,
            symbolPen=pg.mkPen(color, width=1),
            symbolBrush=pg.mkBrush(color),
            pxMode=True,
            antialias=True,
            autoDownsample=False,
            downsample=1,
            clipToView=False,
        )
        curve.setDynamicRangeLimit(None)
        curve.setZValue(5)
        self.plot.addItem(curve)
        return curve

    def refresh_ports(self) -> None:
        current = self.port_box.currentText()
        self.port_box.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_box.addItems(ports)
        if current in ports:
            self.port_box.setCurrentText(current)

    def toggle_serial(self) -> None:
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
            self.open_button.setText("打开串口")
            return

        if not self.port_box.currentText():
            QMessageBox.warning(self, "串口", "未找到可用串口")
            return

        params = {
            "port": self.port_box.currentText(),
            "baudrate": int(self.baud_box.currentText()),
            "bytesize": serial.EIGHTBITS,
            "parity": serial.PARITY_NONE,
            "stopbits": serial.STOPBITS_ONE,
        }
        self.serial_thread = SerialReader(params)
        self.serial_thread.data_received.connect(self.on_serial_data)
        self.serial_thread.state_changed.connect(self.on_serial_state)
        self.serial_thread.start()

    def on_serial_state(self, opened: bool, message: str) -> None:
        self.append_protocol_log(message)
        self.open_button.setText("关闭串口" if opened else "打开串口")

    def on_serial_data(self, data: bytes) -> None:
        if self.log_file_handle:
            self.log_file_handle.write(data)
            self.log_file_handle.flush()
        self.append_serial_text(data)
        for frame in self.parser.feed(data):
            self.append_protocol_log(f"Receive: {bytes_to_hex(frame.raw)}")
            self.consume_frame(frame.timestamp, frame.payload)

    def consume_frame(self, timestamp: int, payload: bytes) -> None:
        if not payload:
            return
        cmd = payload[0]
        data = payload[1:] if len(payload) > 1 else b""
        self.update_device_info(cmd, data)
        if self.start_timestamp is None:
            self.start_timestamp = timestamp

        updated = False
        for row, item in enumerate(self.series.values()):
            cfg = item.config
            end = cfg.offset + cfg.length
            if end > len(data):
                continue
            value = int.from_bytes(data[cfg.offset:end], "big", signed=cfg.signed)
            item.current = value
            item.maximum = value if item.maximum is None else max(item.maximum, value)
            item.minimum = value if item.minimum is None else min(item.minimum, value)
            item.timestamps.append(timestamp)
            item.values.append(value)
            self.update_table_row(row, item)
            self.update_curve(item, rescale=False)
            updated = True
        if updated:
            self.rescale_y_axis_to_visible_data()

    def update_device_info(self, cmd: int, data: bytes) -> None:
        if cmd == 0x01:
            if len(data) >= 1:
                self.device_fault_label.setText(self.format_device_fault(data[0]))
            if len(data) >= 2:
                self.device_temp_label.setText(str(data[1]))
            if len(data) >= 4:
                battery = int.from_bytes(data[2:4], "big", signed=False)
                self.device_battery_label.setText(str(battery))
        elif cmd == 0x02:
            if len(data) >= 1:
                self.smoke_state_label.setText(self.lookup_text(self.smoke_status_text, data[0]))
            if len(data) >= 2:
                self.smoke_type_label.setText(self.lookup_text(self.smoke_type_text, data[1]))

    @staticmethod
    def lookup_text(items: List[str], index: int) -> str:
        return items[index] if 0 <= index < len(items) else str(index)

    @staticmethod
    def format_device_fault(value: int) -> str:
        faults = []
        if value & 0x01:
            faults.append("低电")
        if value & 0x02:
            faults.append("寿命终结")
        if value & 0x04:
            faults.append("防拆报警")
        return "|".join(faults) if faults else "无"

    def update_table_row(self, row: int, item: SeriesData) -> None:
        values = [
            str(item.current),
            str(item.maximum if item.maximum is not None else 0),
            str(item.minimum if item.minimum is not None else 0),
        ]
        self.table.blockSignals(True)
        for col, value in enumerate(values, 1):
            self.table.item(row, col).setText(value)
        self.table.blockSignals(False)

    def update_curve(self, item: SeriesData, rescale: bool = True) -> None:
        if not item.curve or self.start_timestamp is None:
            return
        x_values = [ts - self.start_timestamp for ts in item.timestamps]
        item.curve.setData(x_values, item.values)
        if rescale:
            self.rescale_y_axis_to_visible_data()

    def rescale_y_axis_to_visible_data(self) -> None:
        if self._rescaling_y_axis:
            return
        values = [
            value
            for item in self.series.values()
            if item.visible
            for value in item.values
        ]
        if not values:
            self.set_y_range(-1, 1)
            return

        min_value = min(values)
        max_value = max(values)
        if min_value == max_value:
            padding = max(abs(min_value) * 0.1, 1)
        else:
            padding = max((max_value - min_value) * 0.12, 1)

        self.set_y_range(min_value - padding, max_value + padding)

    def set_y_range(self, lower: float, upper: float) -> None:
        if lower >= upper:
            upper = lower + 1
        span = upper - lower
        step = self.nice_tick_step(span / 8)
        lower = math.floor(lower / step) * step
        upper = math.ceil(upper / step) * step

        self._rescaling_y_axis = True
        try:
            self.plot.getViewBox().setYRange(lower, upper, padding=0)
        finally:
            self._rescaling_y_axis = False

    @staticmethod
    def nice_tick_step(value: float) -> float:
        if value <= 0:
            return 1
        exponent = math.floor(math.log10(value))
        fraction = value / (10 ** exponent)
        if fraction <= 1:
            nice_fraction = 1
        elif fraction <= 2:
            nice_fraction = 2
        elif fraction <= 5:
            nice_fraction = 5
        else:
            nice_fraction = 10
        return nice_fraction * (10 ** exponent)

    def refresh_series_visibility(self) -> None:
        for item in self.series.values():
            if item.curve:
                item.curve.setVisible(item.visible)
        self.refresh_plot_legend()
        self.rescale_y_axis_to_visible_data()

    def refresh_plot_legend(self) -> None:
        legend = self.plot.getPlotItem().legend
        if legend is None:
            legend = self.plot.addLegend()
        self.legend = legend
        legend.clear()
        for item in self.series.values():
            if item.visible and item.curve:
                legend.addItem(item.curve, item.config.name)
        self.position_plot_legend()

    def position_plot_legend(self) -> None:
        if self.legend:
            self.legend.anchor((1, 0), (1, 0), offset=(-20, 48))

    def table_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 0:
            return
        series = self.series.get(item.text())
        if series and series.curve:
            series.visible = item.checkState() == Qt.Checked
            self.refresh_series_visibility()

    def show_table_context_menu(self, pos) -> None:
        menu = QMenu(self)
        add_action = QAction("添加", self)
        import_action = QAction("导入文件", self)
        clear_action = QAction("清除所有", self)
        export_action = QAction("导出excel", self)

        add_action.triggered.connect(self.add_graph_config)
        import_action.triggered.connect(self.import_log_dialog)
        clear_action.triggered.connect(self.clear_all)
        export_action.triggered.connect(self.export_excel_dialog)

        row = self.table.indexAt(pos).row()
        if row >= 0:
            self.table.selectRow(row)
            edit_action = QAction("编辑", self)
            edit_action.triggered.connect(lambda: self.edit_graph_config(row))
            delete_action = QAction("删除", self)
            delete_action.triggered.connect(lambda: self.delete_graph_config(row))
            menu.addAction(edit_action)
            menu.addAction(delete_action)

        menu.addAction(add_action)
        menu.addAction(import_action)
        menu.addAction(clear_action)
        menu.addAction(export_action)
        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def add_graph_config(self) -> None:
        dialog = GraphConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.save_graph_config(dialog.get_config())
            self.load_graph_configs()

    def edit_graph_config(self, row: int) -> None:
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        series = self.series.get(name_item.text())
        if not series:
            return
        old_name = series.config.name
        dialog = GraphConfigDialog(self, series.config)
        if dialog.exec_() == QDialog.Accepted:
            self.save_graph_config(dialog.get_config(), old_name=old_name)
            self.load_graph_configs()

    def delete_graph_config(self, row: int) -> None:
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        name = name_item.text()
        reply = QMessageBox.question(
            self,
            "删除曲线",
            f"确认删除“{name}”吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        config_path = self.setting_dir / "table.ini"
        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")
        if config.has_section(name):
            config.remove_section(name)
            with open(config_path, "w", encoding="utf-8") as file:
                config.write(file)
        self.load_graph_configs()

    def save_graph_config(self, graph_config: GraphConfig, old_name: Optional[str] = None) -> None:
        config_path = self.setting_dir / "table.ini"
        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")

        if old_name and old_name != graph_config.name:
            config.remove_section(old_name)
        if config.has_section(graph_config.name):
            config.remove_section(graph_config.name)

        config.add_section(graph_config.name)
        config.set(graph_config.name, "偏移", str(graph_config.offset))
        config.set(graph_config.name, "数据长度", str(graph_config.length))
        config.set(graph_config.name, "整形类型", "signed" if graph_config.signed else "unsigned")
        config.set(graph_config.name, "颜色", graph_config.color)

        with open(config_path, "w", encoding="utf-8") as file:
            config.write(file)

    def toggle_raw_log(self) -> None:
        if self.save_check.isChecked():
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存log文件",
                str(self.log_dir / f"{time.strftime('%Y-%m-%d_%H%M%S')}.log"),
                "Log Files (*.log)",
            )
            if not file_path:
                self.save_check.setChecked(False)
                return
            self.log_file_handle = open(file_path, "ab")
        else:
            if self.log_file_handle:
                self.log_file_handle.close()
                self.log_file_handle = None

    def import_log_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "导入log文件", str(self.root), "Log Files (*.log *.txt)")
        if file_path:
            self.import_log(file_path)

    def import_log(self, file_path: str) -> None:
        self.import_log_with_marks(file_path)
        return
        self.clear_all()
        self.append_protocol_log(f"开始导入: {file_path}")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            for frame in iter_log_frames(file):
                self.append_protocol_log(f"Receive: {bytes_to_hex(frame.raw)}")
                self.consume_frame(frame.timestamp, frame.payload)
        self.append_protocol_log("导入完成")

    def import_log_with_marks(self, file_path: str) -> None:
        self.clear_all()
        self.append_protocol_log(f"开始导入 {file_path}")
        parser = FrameParser()
        imported_marks: List[MarkData] = []
        pending_mark: Optional[MarkData] = None
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                timestamp = extract_log_timestamp(line) or int(time.time())
                hex_string = extract_receive_hex(line)
                if hex_string:
                    for frame in parser.feed(hex_to_bytes(hex_string), timestamp):
                        self.append_protocol_log(f"Receive: {bytes_to_hex(frame.raw)}")
                        self.consume_frame(frame.timestamp, frame.payload)
                    continue

                pending_mark = self.parse_imported_mark_line(line, timestamp, pending_mark, imported_marks)
        if pending_mark and pending_mark.end:
            imported_marks.append(pending_mark)
        self.add_imported_marks(imported_marks)
        self.append_protocol_log("导入完成")

    def parse_imported_mark_line(
        self,
        line: str,
        timestamp: int,
        pending_mark: Optional[MarkData],
        imported_marks: List[MarkData],
    ) -> Optional[MarkData]:
        start_match = re.search(r'Graph:\s*mark\s+start\s+"([^"]+)"\s+"([^"]+)"', line)
        if start_match:
            if pending_mark and pending_mark.end:
                imported_marks.append(pending_mark)
            mark = MarkData(name=start_match.group(1), device_id=start_match.group(2), start=timestamp)
            mark.angle = self.extract_angle_from_device_id(mark.device_id)
            return mark

        if pending_mark and "Graph: mark value" in line:
            self.apply_imported_mark_value(pending_mark, line)
            pending_mark.end = timestamp
            return pending_mark

        end_match = re.search(r'Graph:\s*mark\s+end\s+"([^"]+)"', line)
        if pending_mark and end_match:
            pending_mark.name = end_match.group(1) or pending_mark.name
            pending_mark.end = pending_mark.end or timestamp
            imported_marks.append(pending_mark)
            return None

        return pending_mark

    def apply_imported_mark_value(self, mark: MarkData, line: str) -> None:
        values = self.parse_imported_mark_value_fields(line)
        if not values:
            return
        angle = values.get("angle") or mark.angle or self.extract_angle_from_device_id(mark.device_id)
        backup = values.get("backup", "")
        raw_id = values.get("id", "")
        if raw_id:
            mark.device_id = self.compose_imported_device_id(raw_id, backup, angle, mark.device_id)
        if angle:
            mark.angle = angle
        try:
            if values.get("sensity"):
                mark.sensitivity = float(values["sensity"])
        except ValueError:
            pass

    @staticmethod
    def parse_imported_mark_value_fields(line: str) -> Dict[str, str]:
        values: Dict[str, str] = {}
        for token in re.findall(r'"([^"]+)"', line):
            if ":" in token:
                key, value = token.split(":", 1)
                values[key.strip()] = value.strip()
        if values:
            return values

        match = re.search(r"mark\s+value\s+id:(.*?)\s+angle:(\S+)\s+sensity:([0-9.]+)", line)
        if match:
            values["id"] = match.group(1).strip()
            values["angle"] = match.group(2).strip()
            values["sensity"] = match.group(3).strip()
        return values

    @staticmethod
    def extract_angle_from_device_id(device_id: str) -> str:
        if "/" not in device_id:
            return ""
        return device_id.rsplit("/", 1)[1].strip()

    @staticmethod
    def compose_imported_device_id(raw_id: str, backup: str, angle: str, fallback: str) -> str:
        raw_id = raw_id.strip().strip('"')
        if raw_id.endswith("#"):
            raw_id = raw_id[:-1]
        if "#" in raw_id and "/" in raw_id:
            return raw_id

        device = raw_id
        note = backup.strip()
        if "#" in raw_id:
            device, raw_note = raw_id.split("#", 1)
            note = note or raw_note.strip()

        if not device and fallback:
            device = fallback.split("#", 1)[0]
        if not note and "#" in fallback and "/" in fallback:
            note = fallback.split("#", 1)[1].rsplit("/", 1)[0]
        angle = angle or IntegratedTester.extract_angle_from_device_id(fallback) or "Null"
        return f"{device}#{note}/{angle}"

    def add_imported_marks(self, marks: List[MarkData]) -> None:
        for mark in marks:
            if mark.end is None or mark.end <= mark.start:
                continue
            self.marks.append(mark)
            self.add_mark_line(mark, is_start=True)
            self.add_mark_line(mark, is_start=False)

    def export_excel_dialog(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出Excel",
            str(self.output_dir / f"Tester_{time.strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"),
            "Excel Files (*.xlsx)",
        )
        if file_path:
            self.export_excel(file_path)

    def export_excel(self, file_path: str) -> None:
        if not self.series:
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "曲线数据"
        headers = ["标识", "类型", "时间差(s)", "时间"] + list(self.series.keys())
        ws.append(headers)

        first_series = next(iter(self.series.values()))
        for idx, timestamp in enumerate(first_series.timestamps):
            mark = self.find_mark(timestamp)
            row = [
                mark.device_id if mark else "无",
                mark.name if mark else "无",
                timestamp - (self.start_timestamp or timestamp),
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
            ]
            for item in self.series.values():
                row.append(item.values[idx] if idx < len(item.values) else "")
            ws.append(row)

        ws.column_dimensions["D"].width = 22
        wb.save(file_path)
        QMessageBox.information(self, "导出Excel", "导出完成")

    def toggle_mark(self) -> None:
        now = int(time.time())
        if self.current_mark:
            value, ok = QInputDialog.getDouble(self, "灵敏度输入", "请输入灵敏度:", 0.0, 0.0, 100.0, 3)
            self.current_mark.end = now
            if ok:
                self.current_mark.sensitivity = value
            self.current_mark.angle = self.angle_box.currentText()
            self.add_mark_line(self.current_mark, is_start=False)
            self.append_protocol_log(
                f'Graph: mark value id:{self.current_mark.device_id}# '
                f"angle:{self.current_mark.angle} sensity:{self.current_mark.sensitivity or 0}"
            )
            self.current_mark = None
            self.mark_button.setText("标记起点")
            return

        device = self.mark_id.text().strip()
        note = self.mark_note.text().strip()
        device_id = f"{device}#{note}/{self.angle_box.currentText()}" if device else f"无#{note}/{self.angle_box.currentText()}"
        mark = MarkData(name=self.mark_type.currentText(), device_id=device_id, start=now)
        self.marks.append(mark)
        self.current_mark = mark
        self.add_mark_line(mark, is_start=True)
        self.append_protocol_log(f'Graph: mark start "{mark.name}" "{mark.device_id}"')
        self.mark_button.setText("标记终点")

    def add_mark_line(self, mark: MarkData, is_start: bool) -> None:
        if self.start_timestamp is None:
            self.start_timestamp = mark.start
        stamp = mark.start if is_start else mark.end
        if stamp is None:
            return
        line = pg.InfiniteLine(pos=stamp - self.start_timestamp, angle=90, movable=False)
        line.setPen(pg.mkPen("#1f77b4" if is_start else "#d62728", width=1, style=Qt.DashLine))
        self.plot.addItem(line)
        if is_start:
            mark.start_line = line
        else:
            mark.end_line = line
            start_pos = mark.start - self.start_timestamp
            end_pos = mark.end - self.start_timestamp if mark.end is not None else start_pos
            region = pg.LinearRegionItem(
                sorted((start_pos, end_pos)),
                movable=False,
                brush=(0, 0, 0, 45),
            )
            region.setZValue(-10)
            self.plot.addItem(region)
            mark.region = region
            label = pg.TextItem(
                self.format_mark_label(mark),
                anchor=(0.5, 1),
                color=QColor("#222222"),
                border=pg.mkPen("#888888"),
                fill=(255, 255, 255, 210),
            )
            x_range, y_range = self.plot.getViewBox().viewRange()
            self.ensure_mark_label_base(x_range, y_range)
            label.setZValue(25)
            self.plot.addItem(label, ignoreBounds=True)
            mark.label_text = label
            self.update_mark_label_positions()

    @staticmethod
    def format_mark_label(mark: MarkData) -> str:
        return f"{mark.name}-{mark.device_id}"

    def update_mark_label_positions(self) -> None:
        if self.start_timestamp is None or not hasattr(self, "plot"):
            return
        x_range, y_range = self.plot.getViewBox().viewRange()
        y_span = y_range[1] - y_range[0]
        if y_span <= 0:
            return

        font = self.create_mark_label_font(x_range, y_range)
        y_pos = y_range[0] + y_span * 0.02
        for mark in self.marks:
            if not mark.label_text or mark.end is None:
                continue
            start_pos = mark.start - self.start_timestamp
            end_pos = mark.end - self.start_timestamp
            left, right = sorted((start_pos, end_pos))
            if right < x_range[0] or left > x_range[1]:
                mark.label_text.setVisible(False)
                continue

            visible_left = max(left, x_range[0])
            visible_right = min(right, x_range[1])
            x_pos = (visible_left + visible_right) / 2
            mark.label_text.setText(self.format_mark_label(mark))
            mark.label_text.setFont(font)
            mark.label_text.setPos(x_pos, y_pos)
            mark.label_text.setVisible(True)

    def ensure_mark_label_base(self, x_range: List[float], y_range: List[float]) -> None:
        if self.mark_label_base_initialized:
            return
        self.mark_label_base_x_span = max(abs(x_range[1] - x_range[0]), 1e-9)
        self.mark_label_base_y_span = max(abs(y_range[1] - y_range[0]), 1e-9)
        self.mark_label_base_initialized = True

    def create_mark_label_font(self, x_range: List[float], y_range: List[float]) -> QFont:
        self.ensure_mark_label_base(x_range, y_range)
        current_x_span = max(abs(x_range[1] - x_range[0]), 1e-9)
        current_y_span = max(abs(y_range[1] - y_range[0]), 1e-9)
        x_scale = self.mark_label_base_x_span / current_x_span
        y_scale = self.mark_label_base_y_span / current_y_span
        scale = math.sqrt(max(x_scale * y_scale, 1e-9))
        font_size = max(5.0, min(16.0, 6.0 * scale))
        return QFont("Microsoft YaHei", int(round(font_size)))

    def locate_mark(self) -> None:
        target = self.mark_id.text().strip()
        for mark in self.marks:
            if mark.device_id.split("#", 1)[0] == target and mark.end and self.start_timestamp is not None:
                self.plot.setXRange(mark.start - self.start_timestamp, mark.end - self.start_timestamp, padding=0.05)
                return
        QMessageBox.warning(self, "定位", "没有找到对应标记")

    def find_mark(self, timestamp: int) -> Optional[MarkData]:
        for mark in self.marks:
            if mark.end and mark.start <= timestamp <= mark.end:
                return mark
        return None

    def clear_all(self) -> None:
        self.start_timestamp = None
        self.parser = FrameParser()
        self.marks.clear()
        self.current_mark = None
        self.mark_label_base_initialized = False
        self.cursor_x = None
        self.plot.clear()
        self.legend = self.plot.getPlotItem().legend or self.plot.addLegend()
        self.legend.clear()
        for row, item in enumerate(self.series.values()):
            item.current = 0
            item.maximum = None
            item.minimum = None
            item.timestamps.clear()
            item.values.clear()
            item.curve = self.create_series_curve(item.config)
            self.update_table_row(row, item)
        self.refresh_series_visibility()
        self.setup_selection_items()
        self.protocol_browser.clear()
        self.serial_browser.clear()
        self.device_fault_label.setText("无")
        self.device_battery_label.setText("0")
        self.device_temp_label.setText("0")
        self.smoke_state_label.setText("无")
        self.smoke_type_label.setText("无")

    def send_serial_data(self) -> None:
        if self.serial_thread:
            self.serial_thread.send(self.send_edit.text())

    def append_protocol_log(self, text: str) -> None:
        self.protocol_browser.append(str(text).rstrip())

    def append_serial_text(self, data: bytes) -> None:
        text = data.decode("utf-8", errors="replace")
        text = "".join(ch if ch in "\r\n\t" or ord(ch) >= 32 else " " for ch in text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        while "\n\n" in text:
            text = text.replace("\n\n", "\n")
        if not text:
            text = bytes_to_hex(data)

        cursor = self.serial_browser.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.serial_browser.setTextCursor(cursor)
        self.serial_browser.ensureCursorVisible()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        file_path = urls[0].toLocalFile()
        if file_path.lower().endswith(".log"):
            self.import_log(file_path)

    def close(self) -> bool:
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
        if self.log_file_handle:
            self.log_file_handle.close()
            self.log_file_handle = None
        return super().close()
