import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QWidget, QStackedWidget, QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, \
    QFormLayout, QGroupBox, QLineEdit, QSpacerItem, QSizePolicy, QMessageBox, QComboBox, QColorDialog


# 1. 自定义 QLineEdit 类
class ClickableLineEdit(QLineEdit):
    colorSignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 可以在这里初始化一些变量

    # 2. 重写鼠标按下事件
    def mousePressEvent(self, event):
        # 3. 判断是否是鼠标左键
        if event.button() == Qt.LeftButton:
            c = QColorDialog.getColor()
            if c.isValid():
                self.colorSignal.emit(c.name())
                print(c.name())
            print("触发了！鼠标左键点击了输入框")
            # 在这里执行你想要的逻辑
            # self.clear()  # 例如：点击即清空

        # 4. 【重要】调用父类的 mousePressEvent
        # 如果不加这一行，光标将无法定位，右键菜单也会失效
        super().mousePressEvent(event)


class AddFunction(QWidget):
    addSignal = pyqtSignal(str, dict)

    def __init__(self, cmd, param):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)

        self.resize(320, 100)

        self.add_or_edit = cmd
        self.cmd= cmd
        self.param = param

        if self.cmd == 'add':
            self.select_colour = '#000000'
            self.name = QLabel("名称")
            self.name_line_edit = QLineEdit()
            self.index = QLabel("偏移")
            self.index_line_edit = QLineEdit()
            self.length = QLabel("数据长度")
            self.length_combox = QComboBox()
            self.length_combox.addItems(['1', '2', '4'])
            self.integer = QLabel("整形类型")
            self.integer_combox = QComboBox()
            self.integer_combox.addItems(['signed', 'unsigned'])
            self.colour = QLabel("颜色")
            # self.colour_line_edit = QLineEdit()
            self.colour_line_edit = ClickableLineEdit(self)
            self.colour_line_edit.setStyleSheet("background-color: black;")
            self.colour_line_edit.colorSignal.connect(self.set_colour)
        else:
            self.select_colour = self.param['颜色']
            self.name = QLabel("名称")
            self.name_line_edit = QLineEdit(self.param['名称'])
            self.index = QLabel("偏移")
            self.index_line_edit = QLineEdit(self.param['偏移'])

            self.length = QLabel("数据长度")
            self.length_combox = QComboBox()
            self.length_combox.addItems(['1', '2', '4'])
            if self.param['数据长度'] == '1':
                self.length_combox.setCurrentIndex(0)
            elif self.param['数据长度'] == '2':
                self.length_combox.setCurrentIndex(1)
            else:
                self.length_combox.setCurrentIndex(2)

            self.integer = QLabel("整形类型")
            self.integer_combox = QComboBox()
            self.integer_combox.addItems(['signed', 'unsigned'])
            if self.param['整形类型'] == 'signed':
                self.integer_combox.setCurrentIndex(0)
            else:
                self.integer_combox.setCurrentIndex(1)

            self.colour = QLabel("颜色")
            self.colour_line_edit = ClickableLineEdit(self)
            self.colour_line_edit.setStyleSheet(f"background-color: {self.param['颜色']}")
            self.colour_line_edit.colorSignal.connect(self.set_colour)

        self.push_button_1 = QPushButton('确认',self)
        self.push_button_1.setStyleSheet("background-color: rgb(255,255,255); color: black;")
        self.push_button_1.setFixedSize(100, 40)
        self.push_button_1.clicked.connect(self.bt1_confirm)

        self.push_button_2 = QPushButton('取消',self)
        self.push_button_2.setStyleSheet("background-color: rgb(255,255,255); color: black;")
        self.push_button_2.setFixedSize(100, 40)
        self.push_button_2.clicked.connect(self.bt2_cancel)

        from_layout = QFormLayout()
        from_layout.addRow(self.name, self.name_line_edit)
        from_layout.addRow(self.index, self.index_line_edit)
        from_layout.addRow(self.length, self.length_combox)
        from_layout.addRow(self.integer, self.integer_combox)
        from_layout.addRow(self.colour, self.colour_line_edit)
        from_layout.addRow(self.push_button_1, self.push_button_2)
        self.setLayout(from_layout)


    def set_colour(self, color):
        self.select_colour = color
        self.colour_line_edit.setStyleSheet(f"background-color: {color}")

    def bt1_confirm(self):
        set_data = {
            '名称': self.name_line_edit.text(),
            '偏移': self.index_line_edit.text(),
            '数据长度': self.length_combox.currentText(),
            '整形类型': self.integer_combox.currentText(),
            '颜色': self.select_colour,
        }
        self.addSignal.emit(self.cmd, set_data)
        self.close()
        print("完成添加")

    def bt2_cancel(self):
        self.close()
        print("退出添加")

if __name__ == '__main__':
    test = QApplication(sys.argv)
    ex = AddFunction(cmd='add', param=None)
    ex.show()
    sys.exit(test.exec_())