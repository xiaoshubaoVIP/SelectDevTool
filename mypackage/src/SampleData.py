import configparser
import os
import time
from pathlib import Path

import serial
import serial.tools.list_ports

from PyQt5 import QtCore
from PyQt5.QtCore import QDir, ws, Qt
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, \
    QComboBox, QLabel, QGridLayout, QSplitter, QRadioButton

from QCustomPlot_PyQt5 import QCustomPlot

from mypackage.src.SerialThread import SerialThread
from mypackage.src.UartSetWidget import UartSetWidget


class SampleData(QWidget):
    def __init__(self):
        super(SampleData, self).__init__()
        self.error = '<font color="red">{}</font>'
        self.warning = '<font color="orange">{}</font>'
        self.valid = '<font color="green">{}</font>'

        # list_ports.comports()函数来获取可用的串口端口
        self.ports = serial.tools.list_ports.comports()
        self.list_port = []
        for port in sorted(self.ports):
            self.list_port.append(port.name)
        self.list_baud = ['4800', '9600', '19200', '115200']
        #读取ini配置文件
        self.ini_path = QtCore.QDir.currentPath() + '/setting/' + 'setting.ini'
        self.conf = configparser.ConfigParser()  # 需要实例化一个ConfigParser对象
        if Path(self.ini_path).is_file():
            self.conf.read(self.ini_path, encoding='utf-8')

        print(self.list_port)
        #串口对象
        self.set_uart_form = None
        self.serial_thread = None

        #设置文件
        self.set_file_path = None

        #实例化按键
        self.push_button_open = QPushButton("打开串口")
        self.push_button_open.setStyleSheet("background-color: rgb(225,225,225); color: black;")
        self.push_button_open.setFixedSize(75, 25)
        self.push_button_open.clicked.connect(self.open_close_uart)

        #串口基本信息
        #port显示
        self.combox_uart_port = QComboBox()
        self.combox_uart_port.setFixedSize(100, 25)
        self.combox_uart_port.setStyleSheet("QComboBox { background-color: white; }")
        self.combox_uart_port.addItems(self.list_port)
        try:
            port_index = self.list_port.index(self.conf['uart']['port'])
        except ValueError as e:
            port_index = 0
        self.combox_uart_port.setCurrentIndex(port_index)
        #baud显示
        self.combox_uart_baud = QComboBox()
        self.combox_uart_baud.setFixedSize(100, 25)
        self.combox_uart_baud.setStyleSheet("QComboBox { background-color: white; }")
        self.combox_uart_baud.addItems(self.list_baud)
        try:
            baud_index = self.list_baud.index(self.conf['uart']['bound'])
        except ValueError as e:
            baud_index = 0
        self.combox_uart_baud.setCurrentIndex(baud_index)

        #设置串口
        self.push_button_set = QPushButton('设置串口')
        self.push_button_set.setStyleSheet("background-color: rgb(225,225,225); color: black;")
        self.push_button_set.setFixedSize(75, 25)
        self.push_button_set.clicked.connect(self.set_uart_function)

        #保存日志
        self.push_button_save = QPushButton('保存日志')
        self.push_button_save.setStyleSheet("background-color: rgb(225,225,225); color: black;")
        self.push_button_save.setFixedSize(75, 25)
        self.push_button_save.clicked.connect(self.show_save_dialog)

        #ascii或hex
        self.radio_button_ascii = QRadioButton('ascii')
        self.radio_button_ascii.setChecked(True)
        self.radio_button_hex = QRadioButton('hex')

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
        stack_layout_1.addWidget(self.combox_uart_port)
        stack_layout_1.addWidget(self.combox_uart_baud)
        stack_layout_1.addWidget(self.radio_button_ascii)
        stack_layout_1.addWidget(self.radio_button_hex)
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


    def open_close_uart(self):

        dict_data = {'Data5':5, 'Data6':6, 'Data7':7, 'Data8':8}
        dict_stop = {'OneStop':1, 'OneAndHalfStop':1.5, 'TwoStop':2}
        dict_parity = {'NoParity':'N', 'EvenParity':'E', 'OddParity':'O', 'SpaceParity':'S', 'MarkParity':'M'}
        dict_uart_set_param = {
                            'port':self.combox_uart_port.currentText(),
                            'baudrate':int(self.combox_uart_baud.currentText()),
                            'bytesize':dict_data.get(self.conf['uart']['data'], 8),
                            'parity':dict_parity.get(self.conf['uart']['parity'], 'N'),
                            'stopbits':dict_stop.get(self.conf['uart']['stop'], 1)
                           }
        if  self.push_button_open.text() == '打开串口':
            self.uart_open_or_close('open',dict_uart_set_param)
        elif self.push_button_open.text() == '关闭串口':
            self.uart_open_or_close('close',dict_uart_set_param)

    def set_uart_function(self):
        self.set_uart_form = UartSetWidget()
        self.set_uart_form.uart_process_signal.connect(self.uart_open_or_close)
        self.set_uart_form.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.set_uart_form.show()

    # @staticmethod
    def uart_open_or_close(self, cmd, param):
        print('串口:',cmd, param)
        if cmd == 'open':
            if not self.serial_thread or not self.serial_thread.isRunning():
                self.serial_thread = SerialThread(param, 'hex' if self.radio_button_hex.isChecked() else 'ascii')
                self.serial_thread.serial_error.connect(self.serial_thread_error_process)
                self.serial_thread.start()
        elif cmd == 'close':
            self.serial_thread.stop()
            self.push_button_open.setText('打开串口')
            self.combox_uart_port.setEnabled(True)
            self.combox_uart_baud.setEnabled(True)
            self.text_edit.append(self.warning.format(f"串口:{self.combox_uart_port.currentText()}已关闭⚠️"))

    def serial_thread_error_process(self, result_msg):
        print('msg:', result_msg)
        if result_msg == '打开串口成功':
            self.push_button_open.setText('关闭串口')
            self.combox_uart_port.setEnabled(False)
            self.combox_uart_baud.setEnabled(False)
            self.text_edit.append(self.valid.format(f"串口:{self.combox_uart_port.currentText()}已打开✅"))
        elif result_msg == '打开串口失败':
            self.text_edit.append(self.error.format(f"串口:{self.combox_uart_port.currentText()}打开❌"))
        else:
            self.text_edit.append(self.warning.format(f"串口:{result_msg}⚠️"))


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