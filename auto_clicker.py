import sys
import time
import logging
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import pyautogui

# 设置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_clicker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# DPI 感知支持
if sys.platform == 'win32':
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
        logger.info("DPI awareness set successfully")
    except Exception as e:
        logger.error(f"Failed to set DPI awareness: {e}")

class ClickerThread(QThread):
    click_performed = pyqtSignal(dict)
    
    def __init__(self, click_count, interval):
        super().__init__()
        self.click_count = click_count
        self.interval = interval
        self.is_running = True
        
    def run(self):
        clicks_performed = 0
        while clicks_performed < self.click_count and self.is_running:
            # 获取当前鼠标位置
            x, y = pyautogui.position()
            
            pyautogui.click(x, y)
            
            click_info = {
                'timestamp': datetime.now(),
                'position': (x, y),
                'click_number': clicks_performed + 1
            }
            self.click_performed.emit(click_info)
            
            clicks_performed += 1
            time.sleep(self.interval / 1000)  # Convert to seconds
            
    def stop(self):
        self.is_running = False

class AutoClickerWindow(QMainWindow):
    def __init__(self):
        logger.debug("Initializing AutoClickerWindow")
        super().__init__()
        self.setWindowTitle("自动点击器")
        self.setFixedSize(400, 300)
        
        self.click_thread = None
        self.click_history = []
        
        # 添加快捷键支持
        self.setup_shortcuts()
        
        self.init_ui()
    
    def setup_shortcuts(self):
        from PyQt6.QtGui import QShortcut, QKeySequence
        # Esc 键停止点击
        self.escape_shortcut = QShortcut(QKeySequence('Esc'), self)
        self.escape_shortcut.activated.connect(self.stop_clicking)
        
        # Ctrl+Q 退出程序
        self.quit_shortcut = QShortcut(QKeySequence('Ctrl+Q'), self)
        self.quit_shortcut.activated.connect(self.close)
        
        # F9 开始点击
        self.start_shortcut = QShortcut(QKeySequence('F9'), self)
        self.start_shortcut.activated.connect(self.start_clicking)
        
        # F10 停止点击
        self.stop_shortcut = QShortcut(QKeySequence('F10'), self)
        self.stop_shortcut.activated.connect(self.stop_clicking)
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 点击次数设置
        clicks_layout = QHBoxLayout()
        clicks_layout.addWidget(QLabel("点击次数:"))
        self.clicks_spinbox = QSpinBox()
        self.clicks_spinbox.setRange(1, 99999)
        self.clicks_spinbox.setValue(10)
        clicks_layout.addWidget(self.clicks_spinbox)
        layout.addLayout(clicks_layout)
        
        # 间隔时间设置
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("点击间隔(毫秒):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(100, 10000)
        self.interval_spinbox.setValue(1000)
        interval_layout.addWidget(self.interval_spinbox)
        layout.addLayout(interval_layout)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始点击")
        self.start_btn.clicked.connect(self.start_clicking)
        self.stop_btn = QPushButton("停止点击")
        self.stop_btn.clicked.connect(self.stop_clicking)
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        layout.addLayout(control_layout)
        
        # 报告按钮
        report_btn = QPushButton("生成报告")
        report_btn.clicked.connect(self.generate_report)
        layout.addWidget(report_btn)
        
        # 添加快捷键说明
        shortcuts_label = QLabel(
            "快捷键说明：\n"
            "F9: 开始点击\n"
            "F10/Esc: 停止点击\n"
            "Ctrl+Q: 退出程序"
        )
        shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(shortcuts_label)
    
    def start_clicking(self):
        logger.debug("Starting clicking")
        self.click_thread = ClickerThread(
            self.clicks_spinbox.value(),
            self.interval_spinbox.value()
        )
        self.click_thread.click_performed.connect(self.record_click)
        self.click_thread.finished.connect(self.clicking_finished)
        
        self.click_thread.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def stop_clicking(self):
        logger.debug("Stopping clicking")
        if self.click_thread:
            self.click_thread.stop()
    
    def clicking_finished(self):
        logger.debug("Clicking finished")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def record_click(self, click_info):
        logger.debug(f"Click recorded: {click_info}")
        self.click_history.append(click_info)
    
    def generate_report(self):
        if not self.click_history:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "暂无点击记录！")
            return
            
        filename = f"click_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("自动点击报告\n")
            f.write("=" * 50 + "\n\n")
            
            for click in self.click_history:
                f.write(f"点击序号: {click['click_number']}\n")
                f.write(f"点击时间: {click['timestamp']}\n")
                f.write(f"点击位置: {click['position']}\n")
                f.write("-" * 30 + "\n")
                
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "成功", f"报告已生成：{filename}")

if __name__ == "__main__":
    try:
        logger.info("Starting application")
        app = QApplication(sys.argv)
        window = AutoClickerWindow()
        window.show()
        logger.info("Application started successfully")
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Critical error in main: {e}", exc_info=True) 