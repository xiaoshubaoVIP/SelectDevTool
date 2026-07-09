import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication, QFileDialog, QMainWindow, QTabWidget

from mypackage.src.SelectDevice import SelectDevice
from mypackage.src.integrated_tester import IntegratedTester


APP_VERSION = "V1.2.7"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.root = self._prepare_runtime_root()
        self.setWindowTitle(f"Tester - {APP_VERSION}")
        icon_path = self.root / "icon" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # self._setup_logging()
        self._setup_menu()

        self.tabs = QTabWidget()
        self.tester_page = IntegratedTester()
        self.select_page = SelectDevice()
        self.tabs.addTab(self.tester_page, "串口曲线")
        self.tabs.addTab(self.select_page, "数据筛选")
        self.setCentralWidget(self.tabs)
        self.resize(1680, 960)

    def _setup_logging(self) -> None:
        log_file = self.root / f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            filename=str(log_file),
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

        def handle_exception(exc_type, exc_value, exc_traceback):
            logging.error("未捕获异常:", exc_info=(exc_type, exc_value, exc_traceback))

        sys.excepthook = handle_exception
        logging.info("========== DeviceSelect started ==========")

    def _prepare_runtime_root(self) -> Path:
        if getattr(sys, "frozen", False):
            root = Path(sys.executable).resolve().parent
            os.chdir(root)
            bundle_root = Path(getattr(sys, "_MEIPASS", root))
            for dirname in ("setting", "icon"):
                target = root / dirname
                source = bundle_root / dirname
                if not target.exists() and source.exists():
                    shutil.copytree(source, target)
            return root
        return Path(os.getcwd())

    def _setup_menu(self) -> None:
        file_menu = self.menuBar().addMenu("文件")

        import_action = QAction("导入log", self)
        import_action.triggered.connect(self.tester_import_log)
        file_menu.addAction(import_action)

        export_action = QAction("导出曲线Excel", self)
        export_action.triggered.connect(self.tester_export_excel)
        file_menu.addAction(export_action)

        setting_menu = self.menuBar().addMenu("设置")
        open_setting_action = QAction("打开筛选配置", self)
        open_setting_action.triggered.connect(self.open_filter_setting)
        setting_menu.addAction(open_setting_action)

    def tester_import_log(self) -> None:
        self.tabs.setCurrentWidget(self.tester_page)
        self.tester_page.import_log_dialog()

    def tester_export_excel(self) -> None:
        self.tabs.setCurrentWidget(self.tester_page)
        self.tester_page.export_excel_dialog()

    def open_filter_setting(self) -> None:
        setting_path = self.root / "setting" / "setting.xlsx"
        if setting_path.exists():
            os.startfile(setting_path)
            return
        QFileDialog.getOpenFileName(self, "打开设置文件", str(self.root / "setting"), "Excel Files (*.xlsx)")

    def closeEvent(self, event) -> None:
        self.tester_page.close()
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
