import configparser
import os
import sys
from contextlib import nullcontext
from pathlib import Path
# from unittest.mock import inplace

import numpy as np
import pandas as pd
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import *
from pandas.core.interchange.dataframe_protocol import DataFrame


class TableSet(QWidget):
    def __init__(self):
        super().__init__()
        #super(TableWidget, self).__init__(parent)

        self.stock_data = None
        self.list_code = []
        self.tableWidget = None
        self.add_class = None
        self.add_action = QAction("添加", self)
        self.edit_action = QAction("编辑", self)
        self.delete_action = QAction("删除", self)
        # self.set_action = QAction("设置规则", self)

        self.add_action.triggered.connect(self.add_function)
        self.edit_action.triggered.connect(self.edit_function)
        self.delete_action.triggered.connect(self.delete_function)
        # self.set_action.triggered.connect(self.set_function)

        # 获取当前目录的上一级
        temp_path = QDir.currentPath()
        temp_path = QDir(temp_path)
        if temp_path.cdUp():
            self.path = temp_path.absolutePath()+'/setting/'
            if not os.path.isdir(self.path):
                os.mkdir(self.path)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("QTableWidget例子")
        self.resize(480,300)
        layout=QHBoxLayout()

        #实现的效果是一样的，四行三列，所以要灵活运用函数，这里只是示范一下如何单独设置行列
        self.tableWidget=QTableWidget(1,8)

        # TableWidget = QTableWidget()
        # TableWidget.setRowCount(4)
        # TableWidget.setColumnCount(3)

        #设置水平方向的表头标签与垂直方向上的表头标签，注意必须在初始化行列之后进行，否则，没有效果
        self.tableWidget.setHorizontalHeaderLabels(['名称','当前值','最大值', '最小值'])
        #Todo 优化1 设置垂直方向的表头标签
        #self.tableWidget.setVerticalHeaderLabels(['行1', '行2', '行3', '行4'])

        #TODO 优化 2 设置水平方向表格为自适应的伸缩模式
        #self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        #TODO 优化3 将表格变为禁止编辑
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        #TODO 优化 4 设置表格整行选中
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)

        #TODO 优化 5 将行与列的高度设置为所显示的内容的宽度高度匹配
        # QTableWidget.resizeColumnsToContents(self.tableWidget)
        # QTableWidget.resizeRowsToContents(self.tableWidget)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()

        #TODO 优化 6 表格头的显示与隐藏
        #self.tableWidget.verticalHeader().setVisible(False)
        #self.tableWidget.horizontalHeader().setVisible(False)

        #TOdo 优化7 在单元格内放置控件
        # comBox=QComboBox()
        # comBox.addItems(['男','女'])
        # comBox.addItem('未知')
        # comBox.setStyleSheet('QComboBox{margin:3px}')
        # self.tableWidget.setCellWidget(0,1,comBox)
        #
        # searchBtn=QPushButton('修改')
        # searchBtn.setDown(True)
        # searchBtn.setStyleSheet('QPushButton{margin:3px}')
        # self.tableWidget.setCellWidget(0,2,searchBtn)

        #TODO 优化 8 添加数据,表格字体居中显示
        self.load_table_ini()

        #调用所有接口居中显示
        self.set_table_widget_contents_center(remove_flag=False)

        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

        #TabelWidget鼠标点击事件
        #self.tableWidget.cellClicked.connect(self.onCellClicked)
        #self.tableWidget.itemClicked.connect(self.onItemClicked)

        #右击事件
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    # 两种方法读取csv文件显示到table widget
    # 方法1 pandas库读取csv文件
    # 方法2 使用CSV数据填充QTableWidget
    def load_table_ini(self):
        self.tableWidget.clear()     # 清空原有表格内容

        #读取ini配置文件
        table_ini_path = QtCore.QDir.currentPath() + '/setting/' + 'table.ini'
        conf = configparser.ConfigParser()  # 需要实例化一个ConfigParser对象
        if Path(table_ini_path).is_file():
            print('table.ini存在')
            conf.read(table_ini_path, encoding='utf-8')
        else:
            print("table.ini不存在")
            conf.add_section('示例')
            conf.set('示例','当前值', '6666')
            conf.set('示例', '最大值', '8888')
            conf.set('示例', '最小值', '1111')

            with open(table_ini_path, 'w', encoding='utf-8') as f:
                conf.write(f)

        # input_table_rows = input_table.shape[0]  # 获取表格行数
        # input_table_columns = input_table.shape[1]  # 获取表格列数
        # input_table_header = input_table.columns.values.tolist()  # 获取表头
        # ###===========读取表格，转换表格，==============================
        # ###===========给tableWidget设置行列表头========================
        # self.tableWidget.setColumnCount(input_table_columns)  # 设置表格列数
        # self.tableWidget.setRowCount(input_table_rows)  # 设置表格行数
        # self.tableWidget.setHorizontalHeaderLabels(input_table_header)  # 给tablewidget设置行列表头
        # ###===========遍历表格每个元素，同时添加到tableWidget中===========
        # for i in range(input_table_rows):  # 行循环
        #     input_table_rows_values = input_table.iloc[[i]]  # 读入一行数据
        #     input_table_rows_values_array = np.array(input_table_rows_values)  # 将该行数据放入数组中
        #     input_table_rows_values_list = input_table_rows_values_array.tolist()[0]  # 将该数组转换为列表
        #     for j in range(input_table_columns):  # 列循环
        #         input_table_items_list = input_table_rows_values_list[j]  # 行列表中的每个元素放入列列表中
        #         ###==============将遍历的元素添加到tableWidget中并显示=======================
        #         input_table_items = str(input_table_items_list)  # 该数据转换成字符串
        #         new_item = QTableWidgetItem(input_table_items)  # 该字符串类型的数据新建为tableWidget元素
        #         new_item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 显示为水平居中、垂直居中
        #         self.tableWidget.setItem(i, j, new_item)  # 在表格第i行第j列显示newItem元素


    def set_table_widget_contents_center(self, remove_flag):
        data = []
        for row in range(self.tableWidget.rowCount()):
            row_data = []
            for col in range(self.tableWidget.columnCount()):
                self.tableWidget.resizeColumnsToContents()
                item = self.tableWidget.item(row,col)
                if item:#需要加入判断，否则空item会导致死机
                    # print(row,col,item.text())
                    item.setTextAlignment(Qt.AlignCenter)
                    row_data.append(item.text())
                else:
                    row_data.append(None)
            data.append(row_data)

        if remove_flag:
            if data[0][0] == '示例模板':
                self.tableWidget.removeRow(0)
                del data[0]
        self.list_code = data
        # self.stock_data = GetStockDataCycle(self.list_code, cycle_flag=True, frequency=1000)
        # self.stock_data.FreshSignal.connect(self.fresh_stock_data)
        return data

    def save_csv(self):
        print()


    def show_context_menu(self, pos):
        print('右击')
        select_row = self.tableWidget.currentRow()
        print(select_row)


        # 转换坐标系
        row_num = None
        for i in self.tableWidget.selectionModel().selection().indexes():
            row_num = i.row()

        if row_num == select_row:
            print('行号:')
            print(row_num)
            menu = QMenu(self)
            menu.addAction(self.add_action)
            menu.addAction(self.edit_action)
            menu.addAction(self.delete_action)
            # menu.addAction(self.set_action)
            menu.addAction(self.output_action)
            # menu.exec(self.viewport().mapToGlobal(pos))
            print(QCursor.pos())
            menu.exec_(QCursor.pos())
            print('右击事件')


    #添加股票
    def add_function(self):
        print('添加事件')
        self.add_class = addFunction(add_or_edit='add', str1=None, str2=None, str3=None)
        self.add_class.addSignal.connect(self.add_edit_function_ok)
        self.add_class.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.add_class.show()

    @staticmethod
    def edit_function(self):
        print('编辑事件')


    # 删除股票
    @staticmethod
    def delete_function(self):
        print('删除')

    @staticmethod
    def add_edit_function_ok(self, add_data):
        print('添加完成')


if __name__ == '__main__':
    app=QApplication(sys.argv)
    win=TableWidget(None)
    win.show()
    sys.exit(app.exec_())

