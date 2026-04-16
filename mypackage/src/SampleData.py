import os
import time

import serial
from PyQt5 import QtCore
from PyQt5.QtCore import QDir, ws, Qt
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, \
    QComboBox, QLabel, QGridLayout, QSplitter

from QCustomPlot_PyQt5 import QCustomPlot

from mypackage.src.UartSetWidget import UartSetWidget


class SampleData(QWidget):
    def __init__(self):
        super(SampleData, self).__init__()
        self.error = '<font color="red">{}</font>'
        self.warning = '<font color="orange">{}</font>'
        self.valid = '<font color="green">{}</font>'

        #串口对象
        self.set_uart_form = None
        self.ser = None

        #设置文件
        self.set_file_path = None

        #实例化按键
        self.push_button_open = QPushButton("打开串口")
        self.push_button_open.setStyleSheet("background-color: rgb(225,225,225); color: black;")
        self.push_button_open.setFixedSize(60, 25)
        self.push_button_open.clicked.connect(self.open_close_uart)

        #串口基本信息
        self.label_uart_port = QLabel(str('COM3'))
        self.label_uart_port.setFixedSize(40, 25)
        self.label_uart_port.setStyleSheet("QLabel { background-color: white; }")
        self.label_uart_baud = QLabel(str('9600'))
        self.label_uart_baud.setFixedSize(40, 25)
        self.label_uart_baud.setStyleSheet("QLabel { background-color: white; }")

        #设置串口
        self.push_button_set = QPushButton('设置串口')
        self.push_button_set.setStyleSheet("background-color: rgb(225,225,225); color: black;")
        self.push_button_set.setFixedSize(100, 25)
        self.push_button_set.clicked.connect(self.set_uart_function)

        #保存日志
        self.push_button_save = QPushButton('保存日志')
        self.push_button_save.setStyleSheet("background-color: rgb(225,225,225); color: black;")
        self.push_button_save.setFixedSize(100, 25)
        self.push_button_save.clicked.connect(self.show_save_dialog)

        #实例化textEdit并加入布局
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("QTextEdit { background-color: white; }")


        self.customPlot = QCustomPlot(self)
        # self.gridLayout = QGridLayout(self).addWidget(self.customPlot)
        # add two new graphs and set their look:
        self.customPlot.addGraph()
        self.customPlot.graph(0).setPen(QPen(Qt.blue))  # line color blue for first graph
        self.customPlot.graph(0).setBrush(
            QBrush(QColor(0, 0, 255, 20)))  # first graph will be filled with translucent blue
        self.customPlot.addGraph()
        self.customPlot.graph(1).setPen(QPen(Qt.red))  # line color red for second graph


        #布局
        stack_main_layout = QVBoxLayout()
        stack_layout_1 = QHBoxLayout()
        stack_layout_2 = QHBoxLayout()
        # 1. 创建一个水平方向的 QSplitter
        splitter = QSplitter(Qt.Horizontal)

        #并加入布局
        stack_layout_1.addWidget(self.push_button_open)
        stack_layout_1.addWidget(self.label_uart_port)
        stack_layout_1.addWidget(self.label_uart_baud)
        stack_layout_1.addWidget(self.push_button_set)
        stack_layout_1.addWidget(self.push_button_save)
        stack_layout_1.setAlignment(QtCore.Qt.AlignLeft)

        splitter.addWidget(self.text_edit)
        splitter.addWidget(self.customPlot)

        #设置初始大小比例，例如 1:1
        splitter.setSizes([1000, 2000])
        # splitter.setStretchFactor(5, 10)

        stack_layout_2.addWidget(splitter)
        stack_main_layout.addLayout(stack_layout_1)
        stack_main_layout.addLayout(stack_layout_2)
        self.setLayout(stack_main_layout)

    @staticmethod
    def open_close_uart(self):
        # self.set_uart_form = UartSetWidget()
        print("open and close")

    def set_uart_function(self):
        self.set_uart_form = UartSetWidget()
        self.set_uart_form.uart_process_signal.connect(self.uart_process_signal)
        self.set_uart_form.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.set_uart_form.show()

    # @staticmethod
    def uart_process_signal(self, cmd, param):
        print('串口参数:',param)
        self.ser = serial.Serial()  # 配置串口参数
        self.ser.port = param['port']
        self.ser.baudrate = param['baudrate']
        self.ser.bytesize = param['bytesize']
        self.ser.parity = param['parity']
        self.ser.stopbits = param['stopbits']
        self.ser.timeout = 1

        print(f"串口: {self.ser.name}", self.ser.baudrate, self.ser.bytesize, self.ser.parity, self.ser.stopbits, self.ser.timeout)

        if cmd == 'close':
            print("串口已连接，关闭")
            self.ser.close()
        elif cmd == 'open':
            try:
                print("串口被打开")
                self.ser.open()
            except serial.SerialException as e:
                print(f"操作串口时出现错误: {e}")

    def get_dir(self):
        dialog = QFileDialog()
        dialog.options = QFileDialog.Options()
        dialog.options |= QFileDialog.ShowDirsOnly
        # dialog.setFileMode(QFileDialog.ExistingFiles)
        folder_path = dialog.getExistingDirectory(self, "选择文件夹", options=dialog.options)

        if folder_path:
            print(f"选择的文件夹：{folder_path}")
            self.current_path = folder_path
            self.line_edit_path.setText(folder_path)

    def show_save_dialog(self):
        #获取当前时间作为文件名
        timestamp = time.time()
        local_time = time.localtime(timestamp)
        formatted_time = time.strftime('%Y-%m-%d_%H%M%S', local_time)

        # 使用 os.path.normpath 规范化路径，避免非法字符
        default_dir = os.path.normpath(QtCore.QDir.currentPath() + '/save/')
        default_file = self.label_uart_port.currentText() + formatted_time + '.txt'
        full_path = os.path.join(default_dir, default_file)  # 使用 os.path.join 处理路径分隔符

        print("保存路径:", default_dir)

        # 确保目录存在，exist_ok=True 避免重复创建错误
        os.makedirs(default_dir, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '保存 Excel 文件',
            full_path,
            'Excel Files (*.txt)'
        )

        if file_path:
            print("确认保存:",file_path)
            self.save_file(file_path)
        else:
            print("取消保存")

    def save_file(self, save_file):
        try:
            print(self.df)
            print("✅ 文件写入成功！")
        except Exception as e:
            print(f"❌ 写入失败，错误信息: {e}")
            self.text_edit.append(self.error.format("写入excel失败，确保文件在关闭状态❌"))

        # 请求完成
        self.text_edit.append(self.valid.format("刷选完成✅ "))