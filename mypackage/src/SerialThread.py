from PyQt5.QtCore import QThread,pyqtSignal
import serial
from requests.compat import chardet


class SerialThread(QThread):
    # 用于发送串口数据接收信号
    data_received = pyqtSignal(str)
    # 串口打开/接收异常
    serial_error = pyqtSignal(str)

    def __init__(self, serial_param, data_format):
        super(SerialThread, self).__init__()
        #串口参数
        self.serial_param = serial_param

        # 串口已经运行标志位
        self.running = False
        # 串口
        self.serial = None
        # 数据格式
        self.__date_format = data_format
        # 发送开启追加换行
        self.__auto_line = True
        print(self.serial_param, self.__date_format)

    @property
    def date_format(self):
        """
        #把一个getter方法变成属性
        :return:
        """
        return self.__date_format

    @date_format.setter
    def date_format(self, value):
        if not isinstance(value, str):
            raise ValueError('date_format must be an str')
        if value not in ['hex', 'ascii']:
            raise ValueError('date_format must in [hex,ascii]')
        self.__date_format = value

    def run(self):
        if self.running:
            return
        try:
            # 建立一个串口
            with serial.Serial(port = self.serial_param['port'],
                               baudrate = self.serial_param['baudrate'],
                               parity = self.serial_param['parity'],
                               bytesize = self.serial_param['bytesize'],
                               stopbits = self.serial_param['stopbits'],
                               timeout=1) as self.serial:
                self.running = True
                self.serial_error.emit("打开串口成功")
                while self.running:
                    data = self.__read_data__()
                    if data:
                        self.data_received.emit(data)
        except Exception as e:
            print("打开串口时失败：", e)
            self.serial_error.emit("打开串口失败")

    def stop(self):
        self.running = False
        self.wait()

    def __read_data__(self):
        if self.serial is None or not self.serial.isOpen():
            return

        try:
            # 读取串口数据 例如：b'DDR V1.12 52218f4949 cym 23/07/0'
            byte_array = self.serial.readline()
            if len(byte_array) == 0:
                return None
            # ascii显示
            if self.__date_format == 'ascii':
                # 串口接收到的字符串为b'ABC',要转化成unicode字符串才能输出到窗口中去
                data_str = byte_array.decode(encoding='utf-8', errors='ignore')
            else:
                # 串口接收到的字符串为b'ZZ\x02\x03Z'，要转换成16进制字符串显示
                data_str = ' '.join(format(x, '02x') for x in byte_array)
                if self.__auto_line:
                    data_str += '\r\n'
            return data_str
        except Exception as e:
            print("接收数据异常：", e)
            self.serial_error.emit("接收数据异常")

    def send_data(self, data: str):
        if not self.running:
            self.serial_error.emit("请先打开串口")
            return

        # hex发送 比如：5a 5a 02 03 5a -> b'ZZ\x02\x03Z'
        if self.__date_format == 'hex':
            data_str = data.strip()
            send_list = []
            while data_str != '':
                try:
                    num = int(data_str[0:2], 16)
                except ValueError:
                    self.serial_error.emit('请输入十六进制数据，以空格分开!')
                    return
                data_str = data_str[2:].strip()
                send_list.append(num)
            if self.__auto_line:
                send_list.append(0x0d)
                send_list.append(0x0a)
            byte_array = bytes(send_list)
        else:
            if self.__auto_line:
                data += '\r\n'
            # ascii发送 比如：'ABC' -> b'ABC'
            byte_array = data.encode('utf-8')

        try:
            self.serial.write(byte_array)
        except Exception as e:
            print("发送失败", e)
            self.serial_error.emit('发送失败')


