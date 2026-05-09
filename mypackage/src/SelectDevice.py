import os
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PyQt5 import QtCore
from PyQt5.QtCore import QDir, ws
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, \
    QComboBox, QLabel
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Alignment, Font, Border, Side
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
            return

        data = pd.DataFrame()
        #通过修改index属性更改行名称
        data.index = ['通用-A通道校机差值', '通用-B通道校机差值', '通用-B初始增量',
            'UL烟雾-灵敏度', 'UL烟雾-增量比值', 'UL烟雾-比值变化率', 'UL烟雾-计数', 'UL烟雾-PPM', 'UL烟雾-平均值', 'UL烟雾-方差',
            'PU烟雾-灵敏度', 'PU烟雾-增量比值', 'PU烟雾-比值变化率', 'PU烟雾-计数', 'PU烟雾-PPM', 'PU烟雾-平均值', 'PU烟雾-方差',
            '油烟-增量比值', '油烟-比值变化率', '油烟-计数', '油烟-PPM', '油烟-平均值',  '油烟-方差', '油烟-结束时红光增量',
            '混合烟-数组最小值', '混合烟-数组最大值', '混合烟-比值最小值', '混合烟-比值最大值']

        #设备状态
        states_index = 0
        states_bit_start = 12 + states_index * 3
        # A增量
        increment_a_index = 17
        increment_a_bit_start = 12 + increment_a_index * 3
        # B增量
        increment_b_index = 34
        increment_b_bit_start = 12 + increment_b_index * 3
        # 增量比值
        increment_ration_list = []
        increment_index = 36
        increment_bit_start = 12 + increment_index*3
        # 比值变化率
        ration_of_change_list = []
        ration_index = 38
        ration_bit_start = 12 + ration_index*3
        # 计数
        rise_cnt_list = []
        rise_index = 40
        rise_bit_start = 12 + rise_index*3
        # 均值
        average_list = []
        average_index = 42
        average_bit_start = 12 + average_index*3
        # 方差
        variance_list = []
        variance_index = 44
        variance_bit_start = 12 + variance_index*3
        # ppm值
        ppm_list = []
        ppm_index = 5
        ppm_bit_start = 12 + ppm_index*3


        calc_flag = False
        alarm_flag = False

        dev_name = None
        dev_column_min = None
        dev_column_max = None
        dev_column_mean = None
        test_name = None

        for log_file in log_files:
            file_full_path = str(path + '/' + log_file)
            with open(file_full_path, "r", encoding="utf-8") as file:
                for line in file.readlines():
                    # print(line.strip())  # 使用strip()方法去除换行符
                    sub_string_start = "Graph: mark start "
                    sub_string_end = "Graph: mark end "
                    if sub_string_start in line: #开始标记，获取设备编号
                        smoke_box_keyword = ['标准烟雾', 'UL烟雾', '灵敏度', '烟箱']
                        pu_test_keyword = ['PU', '聚氨酯', '海绵']
                        oil_test_keyword = ['烹饪', '油烟']

                        if any(k in line for k in smoke_box_keyword):
                            test_name = "UL烟雾"
                        elif any(k in line for k in pu_test_keyword):
                            test_name = "PU烟雾"
                        elif any(k in line for k in oil_test_keyword):
                            test_name = "油烟"
                        elif "混合烟" in line:
                            test_name = "混合烟"

                        pattern1 = r'\d+\#'
                        dev_name = re.findall(pattern1, line)
                        if dev_name is not None:
                            dev_column_min = str(dev_name[0]) + '_min'
                            dev_column_max = str(dev_name[0]) + '_max'
                            dev_column_mean = str(dev_name[0]) + '_mean'
                            data.loc[:, dev_column_min] = 0
                            data.loc[:, dev_column_max] = 0
                            data.loc[:, dev_column_mean] = 0
                            print("开始标记：", dev_name, f"({test_name})")
                    elif sub_string_end in line: #结束标记
                        # print(line.split(sub_string_end, maxsplit=1))
                        print("结束标记")
                    elif dev_name is not None:
                        if "Receive" not in line:
                            continue
                        sub_line = line.split("Receive: ", maxsplit=1)
                        sub_line = sub_line[1].replace('"','')
                        if len(sub_line) > 30:
                            if (alarm_flag == False) and (int('0x' + sub_line[states_bit_start:states_bit_start+2], 16)
                                                                          == 0x07):
                                alarm_flag = True
                                print("报警了")
                            # print("---------------------------------------")
                            # print("增量比值:", int('0x' + sub_line[increment_bit_start:increment_bit_start+2] +
                            #                             sub_line[increment_bit_start + 3:increment_bit_start + 5], 16))
                            # print("比值变化率:", int('0x' + sub_line[ration_bit_start:ration_bit_start+2] +
                            #                             sub_line[ration_bit_start + 3:ration_bit_start + 5], 16))
                            # print("计数:", int('0x' + sub_line[rise_bit_start:rise_bit_start+2] +
                            #                             sub_line[rise_bit_start + 3:rise_bit_start + 5], 16))
                            # print("平均值:", int('0x' + sub_line[variance_bit_start:variance_bit_start+2] +
                            #                             sub_line[variance_bit_start + 3:variance_bit_start + 5], 16))
                            # print("方差:", int('0x' + sub_line[variance_bit_start:variance_bit_start+2] +
                            #                             sub_line[variance_bit_start + 3:variance_bit_start + 5], 16))
                            # print("PPM:", int('0x' + sub_line[ppm_bit_start:ppm_bit_start+2] +
                            #                             sub_line[ppm_bit_start + 3:ppm_bit_start + 5], 16))

                            #增量比值
                            increment_ration_value = int('0x' + sub_line[increment_bit_start:increment_bit_start+2] +
                                                        sub_line[increment_bit_start + 3:increment_bit_start + 5], 16)
                            #增量A
                            increment_a_value = int('0x' + sub_line[increment_a_bit_start:increment_a_bit_start+2] +
                                                    sub_line[increment_a_bit_start + 3:increment_a_bit_start + 5], 16)
                            #增量B
                            increment_b_value = int('0x' + sub_line[increment_b_bit_start:increment_b_bit_start+2] +
                                                    sub_line[increment_b_bit_start + 3:increment_b_bit_start + 5], 16)
                            #比值变化率，有符号
                            byte_data = bytes.fromhex(sub_line[ration_bit_start:ration_bit_start+2] +
                                                            sub_line[ration_bit_start + 3:ration_bit_start + 5])
                            ration_of_change_value = int.from_bytes(byte_data, byteorder='big', signed=True)
                            #计数
                            rise_cnt_value = int('0x' + sub_line[rise_bit_start:rise_bit_start+2] +
                                                            sub_line[rise_bit_start + 3:rise_bit_start + 5], 16)
                            #均值，有符号
                            byte_data = bytes.fromhex(sub_line[average_bit_start:average_bit_start+2] +
                                                            sub_line[average_bit_start + 3:average_bit_start + 5])
                            average_value = int.from_bytes(byte_data, byteorder='big', signed=True)

                            #方差
                            variance_value = int('0x' + sub_line[variance_bit_start:variance_bit_start+2] +
                                                        sub_line[variance_bit_start + 3:variance_bit_start + 5], 16)
                            #ppm值
                            ppm_value = int('0x' + sub_line[ppm_bit_start:ppm_bit_start+2] +
                                                            sub_line[ppm_bit_start + 3:ppm_bit_start + 5], 16)


                            if increment_ration_value == 0 and calc_flag == True:
                                calc_flag = False
                                if len(increment_ration_list) > 2:
                                    print("---------------------------------------")
                                    print(dev_name)
                                    dev_name = None
                                    increment_ration_min = np.min(increment_ration_list)
                                    increment_ration_max = np.max(increment_ration_list)
                                    increment_ration_mean = int(np.mean(increment_ration_list))
                                    print("增量比值: 均值", increment_ration_mean,
                                          "最大值:", increment_ration_max, "最小值:", increment_ration_min)
                                    data.loc[str(test_name) + '-增量比值',dev_column_min] = increment_ration_min
                                    data.loc[str(test_name) + '-增量比值', dev_column_max] = increment_ration_max
                                    data.loc[str(test_name) + '-增量比值', dev_column_mean] = increment_ration_mean

                                    ration_of_change_min = np.min(ration_of_change_list)
                                    ration_of_change_max = np.max(ration_of_change_list)
                                    ration_of_change_mean = int(np.mean(ration_of_change_list))
                                    print("比值变化率: 均值", ration_of_change_mean,
                                          "最大值:", ration_of_change_max, "最小值:", ration_of_change_min)
                                    data.loc[str(test_name) + '-比值变化率',dev_column_min] = ration_of_change_min
                                    data.loc[str(test_name) + '-比值变化率', dev_column_max] = ration_of_change_max
                                    data.loc[str(test_name) + '-比值变化率', dev_column_mean] = ration_of_change_mean


                                    rise_cnt_min = np.min(rise_cnt_list)
                                    rise_cnt_max = np.max(rise_cnt_list)
                                    rise_cnt_mean = int(np.mean(rise_cnt_list))
                                    print("计数: 均值", rise_cnt_mean, "最大值:", rise_cnt_max, "最小值:", rise_cnt_min)
                                    data.loc[str(test_name) + '-计数',dev_column_min] = rise_cnt_min
                                    data.loc[str(test_name) + '-计数', dev_column_max] = rise_cnt_max
                                    data.loc[str(test_name) + '-计数', dev_column_mean] = rise_cnt_mean


                                    average_min = np.min(average_list)
                                    average_max = np.max(average_list)
                                    average_mean = int(np.mean(average_list))
                                    print("平均值: 均值", average_mean, "最大值:", average_max, "最小值:", average_min)
                                    data.loc[str(test_name) + '-平均值',dev_column_min] = average_min
                                    data.loc[str(test_name) + '-平均值', dev_column_max] = average_max
                                    data.loc[str(test_name) + '-平均值', dev_column_mean] = average_mean

                                    variance_min = np.min(variance_list)
                                    variance_max = np.max(variance_list)
                                    variance_mean = int(np.mean(variance_list))
                                    print("方差: 均值", variance_mean, "最大值:", variance_max, "最小值:", variance_min)
                                    data.loc[str(test_name) + '-方差',dev_column_min] = variance_min
                                    data.loc[str(test_name) + '-方差', dev_column_max] = variance_max
                                    data.loc[str(test_name) + '-方差', dev_column_mean] = variance_mean
                                    print("---------------------------------------")
                                increment_ration_list.clear()
                                ration_of_change_list.clear()
                                rise_cnt_list.clear()
                                average_list.clear()
                                variance_list.clear()
                                ppm_list.clear()
                            elif increment_b_value > 200 or calc_flag == True:
                                print("value:", increment_ration_value, increment_a_value, increment_b_value,
                                      ration_of_change_value, rise_cnt_value, average_value, variance_value, ppm_value)
                                if not calc_flag:
                                    calc_flag = True
                                else:#重置后第二次开始计算
                                    increment_ration_list.append(increment_ration_value)
                                    ration_of_change_list.append(ration_of_change_value)
                                    rise_cnt_list.append(rise_cnt_value)
                                    average_list.append(average_value)
                                    variance_list.append(variance_value)
                                    ppm_list.append(ppm_value)


        print("数据:",data)
        self.df = data
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
            print(self.df)
            # 初始化 Workbook
            wb = Workbook()
            wb_s = wb.active
            columns_list = self.df.columns.to_list()

            # --- 样式定义 ---
            # 居中：水平居中，垂直居中
            align_center = Alignment(horizontal='center', vertical='center')
            # 字体：宋体，11号，加粗
            font_header = Font(name='宋体', size=14, bold=True)
            # 边框（可选，通常表头加个边框更好看）
            thin_border = Border(left=Side(style='thin'),
                                 right=Side(style='thin'),
                                 top=Side(style='thin'),
                                 bottom=Side(style='thin'))

            # 1. 需要先写入值
            rows = dataframe_to_rows(self.df, index=True, header=True)
            for r_idx, row in enumerate(rows, 1):  # 从第1行开始计数
                if r_idx == 1:
                    for c_idx in range(0, len(columns_list)):
                        if c_idx > 1:
                            print("c_idx", c_idx, len(columns_list))
                            pattern = r'\d+\#'
                            match = re.search(pattern, str(columns_list[c_idx - 2]))  # 使用 search 更稳妥，或者确保 findall 有结果
                            if match:
                                wb_s.cell(row=1, column=c_idx, value=match.group(0))
                                cell = wb_s.cell(row=1, column=c_idx)   #写入数据时，同时设置单元格样式
                                cell.alignment = align_center
                                cell.font = font_header
                                cell.border = thin_border
                elif r_idx == 2:
                    for c_idx in range(0, len(columns_list), 3):#for in循环， 起始值、终止值和步长
                        print("c_idx", c_idx, len(columns_list))
                        cell = wb_s.cell(row=2, column=c_idx + 2, value='最小值')
                        cell.border = thin_border
                        cell = wb_s.cell(row=2, column=c_idx + 3, value='最大值')
                        cell.border = thin_border
                        cell = wb_s.cell(row=2, column=c_idx + 4, value='平均值')
                        cell.border = thin_border
                else:
                    for c_idx, value in enumerate(row, 1):
                        # 直接通过单元格坐标写入，而不是 append
                        wb_s.cell(row=r_idx, column=c_idx, value=value)
                        if c_idx > 1 and (c_idx-2)%3 == 0:
                            cell = wb_s.cell(row=r_idx, column=c_idx)
                            cell.border = Border(left=Side(style='thin'), right=None, top=None, bottom=None)
                    # for c_idx in range(0, len(columns_list), 3):  # for in循环， 起始值、终止值和步长,2 5 8 11
                    #     cell = wb_s.cell(row=r_idx, column=c_idx + 2)
                    #     cell.border = Border(left=Side(style='thin'), right=None, top=None, bottom=None)

            # 2. 必须执行1写入后，才能合并单元格，写入设备名称
            columns_array = columns_list[::3]
            for index in range(len(columns_array)):
                    wb_s.merge_cells(None, 1, index*3+2, 1, index*3+4)

            # 3. 合并显示设备号
            wb_s.merge_cells('A1:A2')
            wb_s['A1'] = '编号'
            cell = wb_s['A1']
            cell.alignment = Alignment(horizontal='left', vertical='center')

            # 4. 设置首列A的宽度
            wb_s.column_dimensions['A'].width = 24

            wb.save(save_file)
            wb.close()
            print("✅ 文件写入成功！")
            print(self.df)
        except Exception as e:
            print(f"❌ 写入失败，错误信息: {e}")
            self.text_edit.append(self.error.format("写入excel失败，确保文件在关闭状态❌"))

        # 请求完成
        self.text_edit.append(self.valid.format("刷选完成✅ "))