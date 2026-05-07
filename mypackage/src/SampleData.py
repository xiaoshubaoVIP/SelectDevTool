import configparser
import os
import threading
import time
from pathlib import Path

import serial
import serial.tools.list_ports

from PyQt5 import QtCore
from PyQt5.QtCore import QDir, ws, Qt
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, \
    QComboBox, QLabel, QGridLayout, QSplitter, QRadioButton, QMessageBox

from QCustomPlot_PyQt5 import QCustomPlot

from mypackage.src.PlotWidget import PlotWidget
from mypackage.src.SerialThread import SerialThread
from mypackage.src.TableSet import TableSet
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
        self.ini_path = QtCore.QDir.currentPath() + '/setting/' + 'uart.ini'
        self.conf = configparser.ConfigParser()  # 需要实例化一个ConfigParser对象
        if Path(self.ini_path).is_file():
            self.conf.read(self.ini_path, encoding='utf-8')

        print(self.list_port)

        #graph信息
        self.list_graph_info = []

        #串口对象
        self.set_uart_form = None
        self.serial_thread = None

        #设置文件
        self.set_file_path = None

        #实例化按键
        self.push_button_open = QPushButton("打开串口")
        self.push_button_open.setStyleSheet("background-color: rgb(225,225,225); color: black;")
        self.push_button_open.setFixedSize(75, 25)
        self.push_button_open.clicked.connect(self.button_open_close_uart)

        #串口基本信息
        #port显示
        self.combox_uart_port = QComboBox()
        self.combox_uart_port.setFixedSize(75, 25)
        self.combox_uart_port.setStyleSheet("QComboBox { background-color: white; }")
        self.combox_uart_port.addItems(self.list_port)
        try:
            port_index = self.list_port.index(self.conf['uart']['port'])
        except ValueError as e:
            port_index = 0
        self.combox_uart_port.setCurrentIndex(port_index)
        #baud显示
        self.combox_uart_baud = QComboBox()
        self.combox_uart_baud.setFixedSize(75, 25)
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

        #实例化tableWidget
        self.table = TableSet()
        self.table.addResSignal.connect(self.add_success_function)

        #实例化textEdit并加入布局
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("QTextEdit { background-color: white; }")

        #实例化plot
        self.customPlot = PlotWidget()

        #布局
        stack_main_layout = QVBoxLayout()
        stack_layout_1 = QHBoxLayout()
        stack_layout_2 = QHBoxLayout()
        # 1. 创建一个水平方向的 QSplitter
        splitter = QSplitter(Qt.Horizontal)
        splitter_1 = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("QSplitter { background-color: white; }")
        splitter_1.setStyleSheet("QSplitter { background-color: white; }")

        #并加入布局
        stack_layout_1.addWidget(self.push_button_open)
        stack_layout_1.addWidget(self.combox_uart_port)
        stack_layout_1.addWidget(self.combox_uart_baud)
        stack_layout_1.addWidget(self.radio_button_ascii)
        stack_layout_1.addWidget(self.radio_button_hex)
        stack_layout_1.addWidget(self.push_button_set)
        stack_layout_1.addWidget(self.push_button_save)
        stack_layout_1.setAlignment(QtCore.Qt.AlignLeft)

        splitter_1.addWidget(self.table)
        splitter_1.addWidget(self.text_edit)
        splitter_1.setSizes([1000, 1000])

        splitter.addWidget(splitter_1)
        splitter.addWidget(self.customPlot)

        #设置初始大小比例，例如 1:1
        splitter.setSizes([1000, 2000])
        # splitter.setStretchFactor(5, 10)

        stack_layout_2.addWidget(splitter)
        stack_main_layout.addLayout(stack_layout_1)
        stack_main_layout.addLayout(stack_layout_2)
        self.setLayout(stack_main_layout)


    def button_open_close_uart(self):
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
            self.open_or_close_serial('open',dict_uart_set_param)
        elif self.push_button_open.text() == '关闭串口':
            self.open_or_close_serial('close',dict_uart_set_param)

    def set_uart_function(self):
        self.set_uart_form = UartSetWidget()
        self.set_uart_form.uart_process_signal.connect(self.open_or_close_serial)
        self.set_uart_form.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.set_uart_form.show()

    # @staticmethod
    def open_or_close_serial(self, cmd, param):
        print('串口:',cmd, param)
        try:
            port_index = self.list_port.index(str(param['port']))
        except ValueError as e:
            port_index = 0
        self.combox_uart_port.setCurrentIndex(port_index)
        try:
            baud_index = self.list_baud.index(str(param['baudrate']))
        except ValueError as e:
            baud_index = 0
        self.combox_uart_baud.setCurrentIndex(baud_index)
        # self.combox_uart_port.setText(str(param['port']))
        # self.combox_uart_baud.setText(str(param['baudrate']))
        if cmd == 'open':
            if not self.serial_thread or not self.serial_thread.isRunning():
                self.serial_thread = SerialThread(param, 'hex' if self.radio_button_hex.isChecked() else 'ascii')
                self.serial_thread.serial_error.connect(self.serial_thread_error_process)
                self.serial_thread.data_received.connect(self.serial_thread_receive_data_process)
                self.serial_thread.start()
        elif cmd == 'close':
            self.serial_thread.stop()
            self.push_button_open.setText('打开串口')
            self.combox_uart_port.setEnabled(True)
            self.combox_uart_baud.setEnabled(True)
            self.radio_button_ascii.setEnabled(True)
            self.radio_button_hex.setEnabled(True)
            self.push_button_set.setEnabled(True)
            self.push_button_set.setStyleSheet("background-color: rgb(225,225,225); color: black;")
            self.text_edit.append(self.warning.format(f"串口:{self.combox_uart_port.currentText()}已关闭⚠️"))

    def serial_thread_error_process(self, result_msg):
        print('msg:', result_msg)
        if result_msg == '打开串口成功':
            self.push_button_open.setText('关闭串口')
            self.combox_uart_port.setEnabled(False)
            self.combox_uart_baud.setEnabled(False)
            self.radio_button_ascii.setEnabled(False)
            self.radio_button_hex.setEnabled(False)
            self.push_button_set.setEnabled(False)
            self.push_button_set.setStyleSheet("background-color: rgb(225,225,225); color: gray;")
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
        content = self.text_edit.toPlainText()
        if not content:
            QMessageBox.warning(self, "警告", "文本框内容为空，无需保存！")
            return

        #获取当前时间作为文件名
        timestamp = time.time()
        local_time = time.localtime(timestamp)
        formatted_time = time.strftime('%Y-%m-%d_%H%M%S', local_time)

        # 使用 os.path.normpath 规范化路径，避免非法字符
        default_dir = os.path.normpath(QtCore.QDir.currentPath() + '/output/')
        default_file = formatted_time + '.txt'
        full_path = os.path.join(default_dir, default_file)  # 使用 os.path.join 处理路径分隔符

        print("保存路径:", default_dir)

        # 确保目录存在，exist_ok=True 避免重复创建错误
        os.makedirs(default_dir, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '保存 txt 文件',
            full_path,
            'txt files (*.txt)'
        )

        if file_path:
            print("确认保存:",file_path)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.text_edit.append(self.valid.format("保存日志成功✅"))
            except Exception as e:
                print(f"❌ 写入失败，错误信息: {e}")
                self.text_edit.append(self.error.format("保存日志失败，确保文件在关闭状态❌"))
        else:
            print("取消保存")

    def add_success_function(self, info):
        name = info['名称']
        self.list_graph_info.append(info)
        self.text_edit.append(self.valid.format(f"添加绘图对象:{name}✅"))
        self.customPlot.add_graph(info['名称'], info['颜色'])

    @staticmethod
    def get_crc8(buf, length):
        crc = 0
        # 遍历缓冲区
        for j in range(length):
            byte_val = buf[j]

            # 对应 C# 中的 for (i = 0x80; i != 0; i /= 2)
            # 从高位到低位遍历每一位 (128, 64, 32...)
            i = 0x80
            while i != 0:
                if (crc & 0x80) != 0:
                    crc = (crc * 2) & 0xFF  # 左移一位，并强制保留8位
                    crc ^= 0x07
                else:
                    crc = (crc * 2) & 0xFF  # 左移一位

                if (byte_val & i) != 0:
                    crc ^= 0x07

                i //= 2  # 对应 C# 的 i /= 2

        print("crc3:", crc)
        return crc


    def serial_thread_receive_data_process(self, receive_data):

        test_1 = [0x01, 0x02, 0x03, 0x04]
        print("test_1:", self.get_crc8(test_1, len(test_1)))

        test_2 = [1, 2, 3, 4]
        print("test_2:", self.get_crc8(test_2, len(test_2)))

        self.text_edit.append(receive_data)
        hex_str =  ''.join(f'{ord(c):02x}' for c in receive_data)

        print("crc0:", hex_str)
        hex_array = list(bytes.fromhex(hex_str))
        print("crc1:", hex_array)
        crc_calc_array = []
        if hex_array[0] == 0x5A and len(hex_array) > hex_array[1]:
            temp_array = hex_array[0:(hex_array[1]+3)]
            crc_calc_array = temp_array[2:len(temp_array)-1]
            print("crc2:", temp_array)
            print("crc3:", crc_calc_array)

        # crc_data = crc_calc_array[len(hex_array)-1]
        # print("crc3:", crc_data)

        # if self.get_crc8(crc_calc_array, len(crc_calc_array)) == crc_data:                    #crc通过
        #     for info in self.list_graph_info:
        #         char_index = 5 + int(info['偏移'])
        #         data_len = int(info['数据长度'])
        #         target_hex = hex_array[char_index:char_index+data_len]
        #         print(info['名称'], f"0x{target_hex}", char_index, data_len)
                # if target_hex:
                #     decimal_value = int(target_hex, 16)
                #     timestamp = time.time()
                #     self.customPlot.add_data(info['名称'], int(timestamp), decimal_value)