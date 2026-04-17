import configparser
import sys
from pathlib import Path

from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget, QListWidget, QStackedWidget, QHBoxLayout, QFormLayout, QLineEdit, QRadioButton, \
    QLabel, QCheckBox, QApplication, QDesktopWidget, QButtonGroup, QVBoxLayout, QPushButton, QSizePolicy, QMessageBox, \
    QComboBox

import serial.tools.list_ports

import configparser

class UartSetWidget(QWidget):

    uart_process_signal = pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.SubWindow)

        # list_ports.comports()函数来获取可用的串口端口
        self.ports = serial.tools.list_ports.comports()

        #显示数据
        self.list_port = []
        for port in sorted(self.ports):
            self.list_port.append(port.name)
        self.list_baud = ['4800', '9600', '19200', '115200']
        self.dict_data = {'Data5':5, 'Data6':6, 'Data7':7, 'Data8':8}
        self.dict_stop = {'OneStop':1, 'OneAndHalfStop':1.5, 'TwoStop':2}
        self.dict_parity = {'NoParity':'N', 'EvenParity':'E', 'OddParity':'O', 'SpaceParity':'S', 'MarkParity':'M'}


        #读取ini配置文件
        self.ini_path = QtCore.QDir.currentPath() + '/setting/' + 'setting.ini'
        conf = configparser.ConfigParser()  # 需要实例化一个ConfigParser对象
        if Path(self.ini_path).is_file():
            conf.read(self.ini_path, encoding='utf-8')

        # 串口配置下拉框
        self.cb_com = QComboBox()
        self.cb_com.setFixedSize(200, 30)
        self.cb_com.setStyleSheet("QComboBox { background-color: white; }")
        self.cb_com.addItems(self.list_port)
        try:
            port_index = self.list_port.index(conf['uart']['port'])
        except ValueError as e:
            port_index = 0
        self.cb_com.setCurrentIndex(port_index)

        self.cb_baud = QComboBox()
        self.cb_baud.setFixedSize(200, 30)
        self.cb_baud.setStyleSheet("QComboBox { background-color: white; }")
        self.cb_baud.addItems(self.list_baud)
        try:
            baud_index = self.list_baud.index(conf['uart']['bound'])
        except ValueError as e:
            baud_index = 0

        self.cb_baud.setCurrentIndex(baud_index)

        self.cb_data_bit = QComboBox()
        self.cb_data_bit.setFixedSize(200, 30)
        self.cb_data_bit.setStyleSheet("QComboBox { background-color: white; }")
        list_data = list(self.dict_data.keys())
        self.cb_data_bit.addItems(list_data)
        self.cb_data_bit.setCurrentIndex(list_data.index(conf['uart']['data']))

        self.cb_stop_bit = QComboBox()
        self.cb_stop_bit.setFixedSize(200, 30)
        self.cb_stop_bit.setStyleSheet("QComboBox { background-color: white; }")
        list_stop = list(self.dict_stop.keys())
        self.cb_stop_bit.addItems(list_stop)
        self.cb_stop_bit.setCurrentIndex(list_stop.index(conf['uart']['stop']))

        self.cb_parity_bit = QComboBox()
        self.cb_parity_bit.setFixedSize(200, 30)
        self.cb_parity_bit.setStyleSheet("QComboBox { background-color: white; }")
        list_parity = list(self.dict_parity.keys())
        self.cb_parity_bit.addItems(list_parity)
        self.cb_parity_bit.setCurrentIndex(list_parity.index(conf['uart']['parity']))

        self.push_button_1 = QPushButton('连接串口')
        self.push_button_1.setStyleSheet("background-color: rgb(255,255,255); color: black;")
        self.push_button_1.setFixedSize(100, 40)
        self.push_button_1.clicked.connect(self.bt_connect)

        self.push_button_2 = QPushButton('保存配置')
        self.push_button_2.setStyleSheet("background-color: rgb(255,255,255); color: black;")
        self.push_button_2.setFixedSize(100, 40)
        self.push_button_2.clicked.connect(self.bt_save)

        layout = QVBoxLayout(self)
        layout_1 = QVBoxLayout(self)
        layout_1_1 = QHBoxLayout(self)
        layout_1_2 = QHBoxLayout(self)
        layout_1_3 = QHBoxLayout(self)
        layout_1_4 = QHBoxLayout(self)
        layout_1_5 = QHBoxLayout(self)
        layout_2 = QHBoxLayout(self)

        label_com = QLabel("端口")
        label_com.setFixedWidth(100)
        layout_1_1.addWidget(label_com)
        layout_1_1.addWidget(self.cb_com)

        label_baud = QLabel("波特率")
        label_baud.setFixedWidth(100)
        layout_1_2.addWidget(label_baud)
        layout_1_2.addWidget(self.cb_baud)

        label_data_bit = QLabel("数据位")
        label_data_bit.setFixedWidth(100)
        layout_1_3.addWidget(label_data_bit)
        layout_1_3.addWidget(self.cb_data_bit)

        label_stop_bit = QLabel("停止位")
        label_stop_bit.setFixedWidth(100)
        layout_1_4.addWidget(label_stop_bit)
        layout_1_4.addWidget(self.cb_stop_bit)

        label_parity_bit = QLabel("奇偶校验位")
        label_parity_bit.setFixedWidth(100)
        layout_1_5.addWidget(label_parity_bit)
        layout_1_5.addWidget(self.cb_parity_bit)

        layout_1.addLayout(layout_1_1)
        layout_1.addLayout(layout_1_2)
        layout_1.addLayout(layout_1_3)
        layout_1.addLayout(layout_1_4)
        layout_1.addLayout(layout_1_5)

        layout_2.addWidget(self.push_button_1)
        layout_2.addWidget(self.push_button_2)

        layout.addLayout(layout_1)
        layout.addLayout(layout_2)

        self.setLayout(layout)

        self.setWindowTitle('串口设置')
        #self.setFixedSize(1, 1)
        self.show()# 或者show()
        self.setGeometry(300, 100, 360, 240)
        self.center()

    def save_ini(self):
        config = configparser.ConfigParser()  # 需要实例化一个ConfigParser对象
        if Path(self.ini_path).is_file():
            config.read(self.ini_path, encoding='utf-8')
            config.set('uart', 'port', self.cb_com.currentText())
            config.set('uart', 'bound', self.cb_baud.currentText())
            config.set('uart', 'data', self.cb_data_bit.currentText())
            config.set('uart', 'stop',self.cb_stop_bit.currentText())
            config.set('uart', 'parity',  self.cb_parity_bit.currentText())

            with open(self.ini_path, 'w') as configfile:
                config.write(configfile)

    # @staticmethod
    def bt_connect(self):
        dict_uart_set_param = {
                            'port':self.cb_com.currentText(),
                            'baudrate':int(self.cb_baud.currentText()),
                            'bytesize':self.dict_data.get(self.cb_data_bit.currentText(), 8),
                            'parity':self.dict_parity.get(self.cb_parity_bit.currentText(), 'N'),
                            'stopbits':self.dict_stop.get(self.cb_stop_bit.currentText(), 1)
                           }
        self.uart_process_signal.emit('open',dict_uart_set_param)
        self.save_ini()
        self.close()


    #@staticmethod
    def bt_save(self):
        print("保存配置")
        self.save_ini()
        self.close()

    def center(self):
        # 获取屏幕的大小
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口的大小
        size = self.geometry()
        # 将窗口移动到屏幕中央
        self.move(int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2))

def main():
    app = QApplication(sys.argv)
    ex = UartSetWidget()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()