import os
import sys

import PyQt5.QtCore as QtCore
from PyQt5.QtGui import QIcon

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QTextEdit, QMainWindow, QApplication, QAction, \
    QDesktopWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QStackedWidget, QFormLayout

from mypackage.src.SelectDevice import SelectDevice
from mypackage.src.UartSetWidget import UartSetWidget

print("pyqt5:v"+QtCore.QT_VERSION_STR)
print(QtCore.QT_VERSION_STR)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        #设置图标
        self.setWindowIcon(QIcon('./icon/icon.png'))

        #设置菜单栏
        self.ex = None
        self.set_bar()

        #功能模块按键
        self.btn_mod1 = QPushButton("数据采样", self)
        self.btn_mod2 = QPushButton("样机刷选", self)
        self.btn_mod3 = QPushButton("迷宫测试", self)
        self.btn_mod4 = QPushButton("保留", self)

        self.btn_mod1.setFixedSize(80,40)
        self.btn_mod2.setFixedSize(80,40)
        self.btn_mod3.setFixedSize(80,40)
        self.btn_mod4.setFixedSize(80,40)

        self.btn_mod1.setStyleSheet("background-color: rgb(190,226,224); color: black; border-radius: 0px;")
        # self.btn_mod2.setStyleSheet("background-color: rgb(255,255,255); color: black; border-radius: 0px;")
        # self.btn_mod3.setStyleSheet("background-color: rgb(255,255,255); color: black; border-radius: 0px;")
        # self.btn_mod4.setStyleSheet("background-color: rgb(255,255,255); color: black; border-radius: 0px;")
        self.btn_mod2.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod3.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod4.setStyleSheet("background-color: rgb(255,255,255);")

        self.btn_mod1.clicked.connect(self.btn_mod1_clicked)
        self.btn_mod2.clicked.connect(self.btn_mod2_clicked)
        self.btn_mod3.clicked.connect(self.btn_mod3_clicked)
        self.btn_mod4.clicked.connect(self.btn_mod4_clicked)

        #放置一个central_widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        #设置水平布局及标题
        main_layout = QVBoxLayout()
        layout_1 = QHBoxLayout()
        layout_2 = QHBoxLayout()

        #堆栈窗口
        self.stack1 = QWidget(self)
        self.stack2 = SelectDevice()
        self.stack3 = QWidget(self)
        self.stack4 = QWidget(self)

        #stack1组件
        # stack2组件
        self.stack1_ui()
        # stack3组件
        self.stack3_ui()
        # stack4组件
        self.stack4_ui()

        self.Stack = QStackedWidget (self)
        self.Stack.addWidget(self.stack1)
        self.Stack.addWidget(self.stack2)
        self.Stack.addWidget(self.stack3)
        self.Stack.addWidget(self.stack4)
        self.Stack.setStyleSheet("background-color: rgb(190,226,224);")

        #设置窗体的宽高和标题
        self.resize(1680,960)
        self.setWindowTitle("小助手 V1.0")

        #将左侧和右侧布局添加到主水平布局中
        layout_1.addWidget(self.btn_mod1)
        layout_1.addWidget(self.btn_mod2)
        layout_1.addWidget(self.btn_mod3)
        layout_1.addWidget(self.btn_mod4)
        layout_1.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        layout_1.setContentsMargins(0,0,0,0)         #控件到layout之间的距离
        layout_1.setSpacing(0)                        #控件之间的距离

        layout_2.addWidget(self.Stack)

        main_layout.addLayout(layout_1)
        main_layout.addLayout(layout_2)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 控件到layout之间的距离
        main_layout.setSpacing(0)  # 控件之间的距离

        central_widget.setLayout(main_layout)
        #设置窗口的主布局
        self.setCentralWidget(central_widget)

        #调用居中函数
        self.show()
        self.center()

    def btn_mod1_clicked(self):
        self.Stack.setCurrentIndex(0)
        self.btn_mod1.setStyleSheet("background-color: rgb(190,226,224); color: black; border-radius: 0px;")
        self.btn_mod2.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod3.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod4.setStyleSheet("background-color: rgb(255,255,255);")

    def btn_mod2_clicked(self):
        self.Stack.setCurrentIndex(1)
        self.btn_mod1.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod2.setStyleSheet("background-color: rgb(190,226,224); color: black; border-radius: 0px;")
        self.btn_mod3.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod4.setStyleSheet("background-color: rgb(255,255,255);")

    def btn_mod3_clicked(self):
        self.Stack.setCurrentIndex(2)
        self.btn_mod1.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod2.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod3.setStyleSheet("background-color: rgb(190,226,224); color: black; border-radius: 0px;")
        self.btn_mod4.setStyleSheet("background-color: rgb(255,255,255);")

    def btn_mod4_clicked(self):
        self.Stack.setCurrentIndex(3)
        self.btn_mod1.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod2.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod3.setStyleSheet("background-color: rgb(255,255,255);")
        self.btn_mod4.setStyleSheet("background-color: rgb(190,226,224); color: black; border-radius: 0px;")

    def stack1_ui(self):
        layout = QFormLayout()
        layout1 = QHBoxLayout()
        layout1.addWidget(QLabel("敬请期待1"))
        layout.addRow(layout1)
        self.stack2.setLayout(layout)

    def stack3_ui(self):
        layout = QFormLayout()
        layout1 = QHBoxLayout()
        layout1.addWidget(QLabel("敬请期待2"))
        layout.addRow(layout1)
        self.stack3.setLayout(layout)

    def stack4_ui(self):
        layout = QFormLayout()
        layout1 = QHBoxLayout()
        layout1.addWidget(QLabel("敬请期待3"))
        layout.addRow(layout1)
        self.stack4.setLayout(layout)

    def set_bar(self):
        # 实例化主窗口的QMenuBar对象
        bar = self.menuBar()

        # 向菜单栏中添加“文件”
        file = bar.addMenu('文件')
        # 向QMenu小控件中添加按钮，子菜单
        file.addAction('打开文件')
        # 定义响应小控件按钮，并设置快捷键关联到操作按钮，添加到父菜单下
        save = QAction('保存文件', self)
        save.setShortcut('Ctrl+S')
        file.addAction(save)
        # 父菜单下
        quit_ = QAction('退出', self)
        file.addAction(quit_)

        # 向菜单栏中添加“设置”
        menu_set = bar.addMenu('设置')
        uart_set = QAction('串口配置', self)
        file_set = QAction('配置文件', self)
        menu_set.addAction(uart_set)
        menu_set.addAction(file_set)
        menu_set.triggered[QAction].connect(self.set_function)

    def set_function(self, action):
        if action.triggered:
            print(action.text())
            if action.text() == '串口配置':
                print("配置。。。")
                self.ex = UartSetWidget()
                self.ex.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
                self.ex.show()
            elif action.text() == '配置文件':
                temp_path = QtCore.QDir(QtCore.QDir.currentPath())
                set_path = temp_path.absolutePath()+'/setting/'

                if os.path.isdir(set_path):
                    dialog = QFileDialog(self, "打开设置文件")
                    dialog.setDirectory(set_path)
                    dialog.setFileMode(QFileDialog.AnyFile)
                    dialog.setOption(QFileDialog.ReadOnly)

                    if dialog.exec_():
                        select_set_file = dialog.selectedFiles()[0]
                        os.startfile(select_set_file)
                        print(f"选择设置文件：{select_set_file}")
                    else:
                        print("打开设置文件失败")

    def center(self):
        # 获取屏幕的大小
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口的大小
        size = self.geometry()
        # 将窗口移动到屏幕中央
        self.move(int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2))

    def closeEvent(self, event):
        print("复写closeEvent")
        self.stack5.stack_close()
        event.accept()

if __name__ == '__main__':
    # 每一个pyqt程序中都需要有一个QApplication对象，sys.argv是一个命令行参数列表
    app = QApplication(sys.argv)
    # 实例化主窗口并显示
    form = MainWindow()
    form.show()

    # 进入程序的主循环，遇到退出情况，终止程序
    sys.exit(app.exec_())