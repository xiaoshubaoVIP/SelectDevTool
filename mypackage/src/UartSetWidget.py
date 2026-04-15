import sys

from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget, QListWidget, QStackedWidget, QHBoxLayout, QFormLayout, QLineEdit, QRadioButton, \
    QLabel, QCheckBox, QApplication, QDesktopWidget, QButtonGroup, QVBoxLayout, QPushButton, QSizePolicy, QMessageBox
from pandas.io.pytables import Fixed


class UartSetWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint|Qt.SubWindow)
        self.select_data = None
        self.msgBox = None
        self.table_display_data = None

        # 数据
        self.line_edit_com = QLineEdit()
        self.line_edit_baud = QLineEdit()
        self.line_edit_data_bit = QLineEdit()
        self.line_edit_stop_bit = QLineEdit()
        self.line_edit_parity_bit = QLineEdit()

        self.line_edit_com.setPlaceholderText("COM3")
        self.line_edit_baud.setPlaceholderText("9600")
        self.line_edit_data_bit.setPlaceholderText("Data8")
        self.line_edit_stop_bit.setPlaceholderText("OneStop")
        self.line_edit_parity_bit.setPlaceholderText("NoParity")

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

        layout_1_1.addWidget(QLabel("端口"))
        layout_1_1.addWidget(self.line_edit_com)
        layout_1_2.addWidget(QLabel("波特率"))
        layout_1_2.addWidget(self.line_edit_baud)
        layout_1_3.addWidget(QLabel("数据位"))
        layout_1_3.addWidget(self.line_edit_data_bit)
        layout_1_4.addWidget(QLabel("停止位"))
        layout_1_4.addWidget(self.line_edit_stop_bit)
        layout_1_5.addWidget(QLabel("奇偶校验位"))
        layout_1_5.addWidget(self.line_edit_parity_bit)

        layout_1.addLayout(layout_1_1)
        layout_1.addLayout(layout_1_2)
        layout_1.addLayout(layout_1_3)
        layout_1.addLayout(layout_1_4)
        layout_1.addLayout(layout_1_5)

        layout_2.addWidget(self.push_button_1)
        layout_2.addWidget(self.push_button_2)
        layout_2.addWidget(self.push_button_1, alignment=Qt.AlignHCenter)
        layout_2.addWidget(self.push_button_2, alignment=Qt.AlignHCenter)

        layout.addLayout(layout_1)
        layout.addLayout(layout_2)

        self.setLayout(layout)

        self.setWindowTitle('串口设置')
        #self.setFixedSize(1, 1)
        self.show()# 或者show()
        self.setGeometry(300, 100, 720, 480)
        self.center()

    # @staticmethod
    def bt_connect(self):
        print("连接串口")
        self.close()

    #@staticmethod
    def bt_save(self):
        print("保存配置")
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
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()