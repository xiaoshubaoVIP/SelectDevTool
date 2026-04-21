import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QWidget, QStackedWidget, QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, \
    QFormLayout, QGroupBox, QLineEdit, QSpacerItem, QSizePolicy, QMessageBox, QComboBox, QColorDialog


class addFunction(QWidget):
    addSignal = pyqtSignal(dict)

    def __init__(self, add_or_edit):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)

        self.resize(320, 100)

        self.akshare = None
        self.msgBox = None

        self.add_or_edit = add_or_edit


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
        self.colour_line_edit = QLineEdit()
        self.colour_line_edit.setStyleSheet("background-color: black;")
        self.colour_line_edit.textEdited.connect(self.select_color)


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

    @staticmethod
    def select_color(self):
        c = QColorDialog.getColor()
        print(c.name())

    def bt1_confirm(self):
        set_data = {
            '名称': self.name_line_edit.text(),
            '偏移': self.index_line_edit.text(),
            '数据长度': self.length_combox.currentText(),
            '整形类型': self.integer_combox.currentText(),
            '颜色': self.colour_line_edit.text(),
        }
        self.addSignal.emit(set_data)
        self.close()
        print("完成添加")

    def bt2_cancel(self):
        self.close()
        print("退出添加")

if __name__ == '__main__':
    test = QApplication(sys.argv)
    ex = addFunction(add_or_edit='add')
    ex.show()
    sys.exit(test.exec_())