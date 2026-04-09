import os
import time
from pathlib import Path

import pandas as pd
from PyQt5 import QtCore
from PyQt5.QtCore import QDir, ws
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, \
    QComboBox, QLabel
from openpyxl import load_workbook, Workbook
from openpyxl.utils.dataframe import dataframe_to_rows


class SelectDevice(QWidget):
    def __init__(self):
        super(SelectDevice, self).__init__()
        self.error = '<font color="red">{}</font>'
        self.warning = '<font color="orange">{}</font>'
        self.valid = '<font color="green">{}</font>'

        #设置文件
        self.set_file_path = None

        #刷选结果
        self.df = pd.DataFrame()

        #实例化按键
        self.btn = QPushButton("打开需要刷选的目录")
        self.btn.setStyleSheet("background-color: rgb(225,225,225); color: black;")
        self.btn.setFixedHeight(40)
        self.btn.clicked.connect(self.get_dir)

        #文本框设定
        self.current_path = QtCore.QDir.currentPath()
        self.line_edit_path = QLineEdit(str(self.current_path))
        self.line_edit_path.setFixedHeight(40)
        self.line_edit_path.setStyleSheet("QLineEdit { background-color: white; }")

        #加载所有机型
        self.label_device = QLabel("选定机型")
        self.label_device.setStyleSheet("background-color: rgb(225,225,225); color: black;")
        self.label_device.setFixedHeight(40)
        self.cb = QComboBox()
        self.cb.setFixedHeight(40)
        self.cb.setStyleSheet("QComboBox { background-color: white; }")

        #开始按键
        self.push_button_start = QPushButton('开始')
        self.push_button_start.setStyleSheet("background-color: rgb(255,255,255); color: black;")
        self.push_button_start.setFixedSize(100, 40)
        self.push_button_start.clicked.connect(self.start_button)

        #实例化textEdit并加入布局
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("QTextEdit { background-color: white; }")

        # 读设置信息
        set_path = self.current_path + '/setting/'
        if not os.path.isdir(set_path):
            os.mkdir(set_path)
            print("set文件不存在")
            self.text_edit.append(self.error.format("请先在setting目录下添加设置文件❌"))
        else:
            self.set_file_path = Path(set_path + 'setting.xlsx')
            if self.set_file_path.is_file():
                try:
                    excel_file = pd.ExcelFile(self.set_file_path)
                    sheet_names = excel_file.sheet_names
                    self.cb.addItems(sheet_names)

                    print('set文件存在')
                    self.text_edit.append(self.valid.format("set文件存在✅"))
                except FileNotFoundError as e:
                    print(f"设置文件打开失败: {e}")
                    self.text_edit.append(self.error.format(f"设置文件打开失败: {e}❌"))
            else:
                print("set文件不存在")
                self.text_edit.append(self.error.format("设置文件不存在❌"))

        #布局
        stack_main_layout = QVBoxLayout()
        stack_layout_1 = QHBoxLayout()
        stack_layout_2 = QHBoxLayout()

        #并加入布局
        stack_layout_1.addWidget(self.btn)
        stack_layout_1.addWidget(self.line_edit_path)
        stack_layout_1.addWidget(self.label_device)
        stack_layout_1.addWidget(self.cb)
        stack_layout_1.addWidget(self.push_button_start)
        stack_layout_2.addWidget(self.text_edit)
        stack_main_layout.addLayout(stack_layout_1)
        stack_main_layout.addLayout(stack_layout_2)
        self.setLayout(stack_main_layout)


    def get_dir(self):
        # # 1. 实例化对话框
        # dialog = QFileDialog()
        # # 2. 设置标题
        # dialog.setWindowTitle("选择包含log文件的目录")
        # # 3. 关键设置：设置为目录模式
        # dialog.setFileMode(QFileDialog.Directory)
        # # 4. 设置过滤器
        # dialog.setNameFilters(["log文件 (*.log)"])
        # # # 5. (可选) 强制使用 Qt 原生样式而非系统样式，以确保过滤器在所有系统上表现一致
        # dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        #
        # # 6. 执行对话框
        # if dialog.exec_():
        #     # 获取选中的文件夹路径
        #     selected_dir = dialog.selectedFiles()[0]
        #     print(f"你选择的文件夹是: {selected_dir}")
        #
        #     # 你可以在这里进一步确认该文件夹下是否有你想要的文件
        #     # 例如检查该目录下是否存在 .xlsx 文件
        #     dir_obj = QDir(selected_dir)
        #     files = dir_obj.entryList(["*.log"])
        #     if files:
        #         print(f"该目录下包含 {len(files)} 个 log 文件")
        #         self.current_path = selected_dir
        #         self.line_edit_path.setText(selected_dir)
        #     else:
        #         print("该目录下没有找到 log 文件")

        dialog = QFileDialog()
        dialog.options = QFileDialog.Options()
        dialog.options |= QFileDialog.ShowDirsOnly
        # dialog.setFileMode(QFileDialog.ExistingFiles)
        folder_path = dialog.getExistingDirectory(self, "选择文件夹", options=dialog.options)

        if folder_path:
            print(f"选择的文件夹：{folder_path}")
            self.current_path = folder_path
            self.line_edit_path.setText(folder_path)

    def start_button(self):
        print("开始")
        temp_path = QtCore.QDir(self.line_edit_path.text())
        path = temp_path.absolutePath()
        print('目录:'+path)
        self.text_edit.clear()
        # self.text_edit.append('目录:'+path)
        if not os.path.isdir(path):
            print("错误")
            self.text_edit.append(self.error.format("目录错误❌"))
        else:
            print("正常")
            self.text_edit.append(self.valid.format("目录正常✅"))
            txt_files = [file for file in os.listdir(path) if file.endswith(".log")]
            if len(txt_files) > 0:
                self.text_edit.append(self.valid.format("目录存在log文件✅"))
                self.log_process(path, txt_files)
            else:
                self.text_edit.append(self.error.format("未找到log文件❌"))

    def log_process(self, path, log_files):
        sheet_name = self.cb.currentText()
        print(sheet_name)
        try:
            set_data = pd.read_excel(self.set_file_path, sheet_name=sheet_name, dtype=str)  # 以字符串形式打开并读取excel表格
            set_data = pd.DataFrame(set_data)
            print(set_data)
            self.text_edit.append(self.valid.format(sheet_name+"配置文件打开✅"))
        except FileNotFoundError as e:
            self.text_edit.append(self.error.format(sheet_name+"配置文件打开❌"))

        for log_file in log_files:
            file_full_path = str(path + '/' + log_file)
            with open(file_full_path, "r", encoding="utf-8") as file:
                for line in file.readlines():
                    # print(line.strip())  # 使用strip()方法去除换行符
                    sub_string_start = "Graph: mark start "
                    sub_string_end = "Graph: mark end "
                    if sub_string_start in line:
                        print(line.split(sub_string_start, maxsplit=1))
                    elif sub_string_end in line:
                        print(line.split(sub_string_end, maxsplit=1))

        self.show_save_dialog()

    def show_save_dialog(self):
        #获取当前时间作为文件名
        timestamp = time.time()
        local_time = time.localtime(timestamp)
        formatted_time = time.strftime('%Y-%m-%d_%H%M%S', local_time)

        # 使用 os.path.normpath 规范化路径，避免非法字符
        default_dir = os.path.normpath(QtCore.QDir.currentPath() + '/output/')
        default_file = self.cb.currentText() + formatted_time + '.xlsx'
        full_path = os.path.join(default_dir, default_file)  # 使用 os.path.join 处理路径分隔符

        print("保存路径:", default_dir)

        # 确保目录存在，exist_ok=True 避免重复创建错误
        os.makedirs(default_dir, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '保存 Excel 文件',
            full_path,
            'Excel Files (*.xlsx)'
        )

        if file_path:
            print("确认保存:",file_path)
            self.save_file(file_path)
        else:
            print("取消保存")

    def save_file(self, save_file):
        try:
            # 初始化 Workbook
            wb = Workbook()
            wb_s = wb.active

            # 将 DataFrame 转换为行并写入工作表
            for row in dataframe_to_rows(self.df, index=False, header=True):
                wb_s.append(row)

            wb_s.merge_cells('A1:C1')
            wb_s['A1'] = '合并后的内容'
            wb.save(save_file)

            print("✅ 文件写入成功！")
        except Exception as e:
            print(f"❌ 写入失败，错误信息: {e}")
            self.text_edit.append(self.error.format("写入excel失败，确保文件在关闭状态❌"))

        # 请求完成
        self.text_edit.append(self.valid.format("刷选完成✅ "))