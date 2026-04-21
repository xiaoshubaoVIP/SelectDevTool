import configparser
import os
import sys
from contextlib import nullcontext
from pathlib import Path
# from unittest.mock import inplace

import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import *
from pandas.core.interchange.dataframe_protocol import DataFrame

from mypackage.src.TableAddEdit import addFunction


class TableSet(QWidget):
    def __init__(self):
        super().__init__()
        #super(TableWidget, self).__init__(parent)

        self.tableWidget = None
        self.add_or_edit = None

        self.add_action = QAction("添加", self)
        self.edit_action = QAction("编辑", self)
        self.delete_action = QAction("删除", self)
        self.add_action.triggered.connect(self.add_function)
        self.edit_action.triggered.connect(self.edit_function)
        self.delete_action.triggered.connect(self.delete_function)

        # 获取当前目录的上一级
        temp_path = QDir.currentPath()
        temp_path = QDir(temp_path)
        if temp_path.cdUp():
            self.path = temp_path.absolutePath()+'/setting/'
            if not os.path.isdir(self.path):
                os.mkdir(self.path)

        self.table_ini_path = QtCore.QDir.currentPath() + '/setting/' + 'table.ini'
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("QTableWidget例子")
        self.resize(480,300)
        layout=QHBoxLayout()

        #实现的效果是一样的，四行三列，所以要灵活运用函数，这里只是示范一下如何单独设置行列
        self.tableWidget=QTableWidget(0,4)

        # #调用所有接口居中显示
        # self.set_table_widget_contents_center(remove_flag=False)

        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

        #右击事件
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # 加载数据
        self.load_ini_to_table()

    def load_ini_to_table(self):
        # 1. 检查文件是否存在
        if not os.path.exists(self.table_ini_path):
            QMessageBox.warning(self, "错误", f"找不到文件: {self.table_ini_path}")
            return

        # 2. 初始化 ConfigParser 并读取文件
        config = configparser.ConfigParser()
        try:
            config.read(self.table_ini_path, encoding='utf-8')
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")
            return

        # 3. 配置 TableWidget 基础属性
        self.tableWidget.setStyleSheet("background-color: white;")
        # 关闭交替行颜色，否则即使设置了背景色，它也会每隔一行显示一种默认颜色
        self.tableWidget.setAlternatingRowColors(False)

        self.tableWidget.clear()  # 清空旧数据

        # 设置水平方向的表头标签与垂直方向上的表头标签，注意必须在初始化行列之后进行，否则，没有效果
        self.tableWidget.setHorizontalHeaderLabels(["名称", "当前值", "最大值", "最小值"])

        #Todo 优化1 设置垂直方向的表头标签
        #self.tableWidget.setVerticalHeaderLabels(['行1', '行2', '行3', '行4'])

        #TODO 优化 2 设置水平方向表格为自适应的伸缩模式
        #self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        #TODO 优化3 将表格变为禁止编辑
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        #TODO 优化 4 设置表格整行选中
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)

        #TODO 优化 5 将行与列的高度设置为所显示的内容的宽度高度匹配
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()

        # 4. 遍历 INI 文件内容
        # config.sections() 获取所有的节点名，例如 [Serial], [Network]
        sections = config.sections()
        row_index = 0
        for section in sections:
            self.tableWidget.insertRow(row_index)
            options = config.options(section)

            # 控件居中方法：
            checkbox = QCheckBox()              # 定义checkbox控件
            checkbox.setChecked(True)           # 默认全部勾选

            name_label = QLabel(str(section))   # 定义QLabelx控件

            # 1.实例化一个新布局
            item_layout = QtWidgets.QHBoxLayout()
            # 2.在布局里添加checkBox
            item_layout.addWidget(checkbox)
            item_layout.addWidget(name_label)
            # 3.在布局里居中放置checkBox并设置水平居中
            item_layout.setAlignment(Qt.AlignLeft)
            # 4.实例化一个QWidget（控件）
            widget = QtWidgets.QWidget()
            # 5.在QWidget放置布局
            widget.setLayout(item_layout)

            self.tableWidget.setCellWidget(row_index, 0, widget)

            column_index = 1
            for option in options:
                #item = config.get(section, option)
                new_item = QTableWidgetItem(None)
                new_item.setFlags(new_item.flags() ^ Qt.ItemIsEditable)  # 设为只读（可选）
                new_item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 显示为水平居中、垂直居中
                # print(row_index, column_index, item)
                self.tableWidget.setItem(row_index, column_index, new_item)
                column_index = column_index + 1
            row_index = row_index + 1

        # 5. 自动调整列宽
        self.tableWidget.resizeColumnsToContents()

    def show_context_menu(self, pos):
        select_row = self.tableWidget.currentRow()


        # 转换坐标系
        row_num = None
        for i in self.tableWidget.selectionModel().selection().indexes():
            row_num = i.row()

        print('右击', select_row, row_num)

        if row_num == select_row:
            print('行号:', row_num)
            menu = QMenu(self)
            menu.addAction(self.add_action)
            menu.addAction(self.edit_action)
            menu.addAction(self.delete_action)
            print(QCursor.pos())
            menu.exec_(QCursor.pos())
        else:
            print("sss")
            menu = QMenu(self)
            menu.addAction(self.add_action)
            print(QCursor.pos())
            menu.exec_(QCursor.pos())


    #添加
    def add_function(self):
        print('添加事件')
        self.add_or_edit = addFunction(add_or_edit='add')
        self.add_or_edit.addSignal.connect(self.add_edit_function)
        self.add_or_edit.show()

    #编辑
    @staticmethod
    def edit_function(self):
        print('编辑事件')

    # 删除
    def delete_function(self):
        print('删除事件')
        cur_row = self.tableWidget.currentRow()
        item = self.tableWidget.cellWidget(cur_row, 0)
        if item is not None:
            target_label = item.findChild(QtWidgets.QLabel)
            if target_label is not None:
                section_name = target_label.text()
                reply = QMessageBox.question(self, '删除', f'确定删除{section_name}的信息?',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.tableWidget.removeRow(cur_row)

                    config = configparser.ConfigParser()
                    try:
                        config.read(self.table_ini_path, encoding='utf-8')
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")
                        return
                    config.remove_section(section_name)  # 删除
                    # 写入文件
                    with open(self.table_ini_path, 'w', encoding='utf-8') as configfile:
                        config.write(configfile)

    #添加和编辑处理函数
    def add_edit_function(self, res):
        print('添加/编辑:', res)

        section = str(res['名称'])
        row_count = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_count)

        # 控件居中方法：
        checkbox = QCheckBox()  # 定义checkbox控件
        checkbox.setChecked(True)  # 默认全部勾选

        name_label = QLabel(str(section))  # 定义QLabelx控件

        # 1.实例化一个新布局
        item_layout = QtWidgets.QHBoxLayout()
        # 2.在布局里添加checkBox
        item_layout.addWidget(checkbox)
        item_layout.addWidget(name_label)
        # 3.在布局里居中放置checkBox并设置水平居中
        item_layout.setAlignment(Qt.AlignLeft)
        # 4.实例化一个QWidget（控件）
        widget = QtWidgets.QWidget()
        # 5.在QWidget放置布局
        widget.setLayout(item_layout)

        self.tableWidget.setCellWidget(row_count, 0, widget)

        config = configparser.ConfigParser()
        try:
            config.read(self.table_ini_path, encoding='utf-8')
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")
            return

        config.add_section(section)
        # 设置键值对
        config.set(section, '偏移', res['偏移'])
        config.set(section, '数据长度', res['数据长度'])
        config.set(section, '整形类型', res['整形类型'])
        config.set(section, '颜色', res['颜色'])

        # 写入文件
        with open(self.table_ini_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)


if __name__ == '__main__':
    app=QApplication(sys.argv)
    win=TableSet(None)
    win.show()
    sys.exit(app.exec_())

