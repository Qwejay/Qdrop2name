import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                            QWidget, QLabel, QListWidget, QDialog, QComboBox,
                            QRadioButton, QButtonGroup, QHBoxLayout, QFrame, QStackedLayout,
                            QFileDialog, QLineEdit, QScrollArea, QSizePolicy, QGroupBox, QMessageBox, QStatusBar,
                            QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QInputDialog,
                            QGraphicsOpacityEffect, QCheckBox, QToolTip, QAction)

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QTimer, QParallelAnimationGroup
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QPalette, QColor, QIcon
import exif
from PIL import Image
from pillow_heif import register_heif_opener

__app_name__ = "Qdrop2name"
__version__ = "2.0"
__author__ = "QwejayHuang"
__company__ = "QwejayHuang"
__description__ = "文件智能重命名工具"

register_heif_opener()


def get_resource_path(relative_path):
    """获取程序资源绝对路径，兼容 PyInstaller 打包环境"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_config_file_path():
    """获取配置文件的安全存储路径，保障打包与受限目录下的写权限"""
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
    try:
        if os.path.exists(local_path):
            if os.access(local_path, os.W_OK):
                return local_path
        else:
            with open(local_path, "a", encoding="utf-8"):
                pass
            return local_path
    except (IOError, OSError, PermissionError):
        pass
    
    app_dir = os.path.join(os.path.expanduser("~"), f".{__app_name__}")
    try:
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, "settings.json")
    except Exception:
        return local_path


class DropArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.NoFrame)  
        self.setCursor(Qt.PointingHandCursor) 
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 2px dashed #cccccc;
                border-radius: 10px;
            }
            QFrame:hover {
                background-color: #e8e8e8;
                border: 2px dashed #999999;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.label = QLabel("拖放文件或文件夹到这里\n或点击选择文件")
        self.label.setAlignment(Qt.AlignCenter)  
        self.label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                font-weight: bold;
                border: none;
                padding: 20px;
            }
        """)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background-color: #e8e8e8;
                    border: 2px dashed #666666;
                    border-radius: 10px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 2px dashed #cccccc;
                border-radius: 10px;
            }
            QFrame:hover {
                background-color: #e8e8e8;
                border: 2px dashed #999999;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 2px dashed #cccccc;
                border-radius: 10px;
            }
            QFrame:hover {
                background-color: #e8e8e8;
                border: 2px dashed #999999;
            }
        """)
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                if self.is_supported_file(path):
                    files.append(path)
            elif os.path.isdir(path):
                files.extend(self.get_files_from_dir(path))
        if files:
            main_window = self.window()
            if isinstance(main_window, MainWindow):
                main_window.add_files(files)
                total_files = len(main_window.files)
                self.label.setText(f"已选择 {total_files} 个文件")

    def get_files_from_dir(self, dir_path):
        files = []
        for root, _, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if self.is_supported_file(file_path):
                    files.append(file_path)
        return files

    def is_supported_file(self, file_path):
        try:
            if not os.path.exists(file_path) or not os.access(file_path, os.R_OK):
                return False
            
            ext = os.path.splitext(file_path)[1].lower()
            image_extensions = {
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic', '.heif', 
                '.tiff', '.tif', '.webp', '.raw', '.arw', '.cr2', '.nef', 
                '.dng', '.orf', '.sr2', '.rw2'
            }
            video_extensions = {
                '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', 
                '.m4v', '.3gp', '.mpg', '.mpeg', '.mts', '.m2ts'
            }
            main_window = self.window()
            if hasattr(main_window, 'settings') and main_window.settings.get("enable_non_media", False):
                return True
            return ext in image_extensions or ext in video_extensions
        except Exception:
            return False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:  
            self.open_file_dialog()

    def open_file_dialog(self):
        dialog = QFileDialog()
        dialog.setWindowTitle("选择文件")
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter(
            "所有支持的文件 (*.jpg *.jpeg *.png *.gif *.bmp *.heic *.heif *.mp4 *.mov *.avi *.mkv *.wmv *.flv *.webm *.m4v *.3gp);;"
            "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp *.heic *.heif);;"
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.wmv *.flv *.webm *.m4v *.3gp);;"
            "JPEG 图片 (*.jpg *.jpeg);;"
            "PNG 图片 (*.png);;"
            "HEIC 图片 (*.heic *.heif);;"
            "MP4 视频 (*.mp4);;"
            "MOV 视频 (*.mov);;"
            "其他视频 (*.avi *.mkv *.wmv *.flv *.webm *.m4v *.3gp);;"
            "所有文件 (*.*)"
        )
        
        if dialog.exec_():
            files = []
            for path in dialog.selectedFiles():
                if os.path.isfile(path):
                    if self.is_supported_file(path):
                        files.append(path)
                elif os.path.isdir(path):
                    files.extend(self.get_files_from_dir(path))
            
            if files:
                main_window = self.window()
                if isinstance(main_window, MainWindow):
                    main_window.add_files(files)
                    total_files = len(main_window.files)
                    self.label.setText(f"已选择 {total_files} 个文件")

    def show_success(self, count):
        self.label.setText(f"✓ 已重命名 {count} 个文件")
        self.label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 16px;
                font-weight: bold;
                border: none;
                padding: 20px;
            }
        """)
        QTimer.singleShot(3000, self.reset_label)

    def reset_label(self):
        self.label.setText("拖放文件或文件夹到这里\n或点击选择文件")
        self.label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                font-weight: bold;
                border: none;
                padding: 20px;
            }
        """)


class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)
        
        self.animation_group = QParallelAnimationGroup()
        
        self.position_animation = QPropertyAnimation(self, b"geometry")
        self.position_animation.setDuration(150)
        self.position_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        self.animation_group.addAnimation(self.position_animation)
        self.animation_group.addAnimation(self.opacity_animation)
        self.is_hovered = False

    def enterEvent(self, event):
        if not self.is_hovered:
            self.is_hovered = True
            current_geometry = self.geometry()
            self.position_animation.setStartValue(current_geometry)
            self.position_animation.setEndValue(current_geometry.adjusted(0, -2, 0, -2))
            self.opacity_animation.setStartValue(1.0)
            self.opacity_animation.setEndValue(0.8)
            self.animation_group.start()

    def leaveEvent(self, event):
        if self.is_hovered:
            self.is_hovered = False
            current_geometry = self.geometry()
            self.position_animation.setStartValue(current_geometry)
            self.position_animation.setEndValue(current_geometry.adjusted(0, 2, 0, 2))
            self.opacity_animation.setStartValue(0.8)
            self.opacity_animation.setEndValue(1.0)
            self.animation_group.start()


class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.settings = self.load_settings()
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            QLabel {
                color: #333333;
                font-size: 13px;
            }
            QComboBox {
                color: #333333;
                font-size: 13px;
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                min-width: 250px;
                min-height: 32px;
            }
            QComboBox:hover {
                border-color: #999999;
            }
            QComboBox:focus {
                border-color: #999999;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #999999;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #e0e0e0;
                background: white;
                selection-background-color: #f5f5f5;
                selection-color: #333333;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px;
                min-height: 28px;
            }
            QRadioButton {
                color: #333333;
                font-size: 13px;
                padding: 8px 0;
                spacing: 8px;
                min-height: 32px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #e0e0e0;
                border-radius: 9px;
            }
            QRadioButton::indicator:hover {
                border-color: #999999;
            }
            QRadioButton::indicator:checked {
                background-color: #999999;
                border-color: #999999;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 13px;
                background: white;
                min-height: 32px;
            }
            QLineEdit:hover {
                border-color: #999999;
            }
            QLineEdit:focus {
                border-color: #999999;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 7px;
                padding: 7px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333333;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(30, 30, 30, 30)

        template_group = QGroupBox("命名模板")
        template_layout = QVBoxLayout()
        template_layout.setSpacing(16)
        template_layout.setContentsMargins(16, 20, 16, 16)
        
        template_input_layout = QHBoxLayout()
        template_input_layout.setSpacing(12)
        
        self.custom_format_label = QLabel("命名模板")
        self.custom_format_label.setStyleSheet("color: #666666; font-size: 13px;")
        self.custom_format_label.setFixedWidth(80)
        template_input_layout.addWidget(self.custom_format_label)
        
        self.custom_format = QLineEdit()
        self.custom_format.setPlaceholderText("可用变量：{YYYY}年 {MM}月 {DD}日 {HH}时 {mm}分 {SS}秒")
        self.custom_format.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                font-size: 13px;
                min-width: 300px;
                height: 32px;
            }
            QLineEdit:hover {
                border-color: #999999;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        template_input_layout.addWidget(self.custom_format)
        
        help_btn = QPushButton("💡")
        help_btn.setFixedSize(32, 32)
        help_text = """
命名模板说明：

可用变量：
{YYYY} - 年份（如：2025）
{MM} - 月份（如：04）
{DD} - 日期（如：15）
{HH} - 小时（如：12）
{mm} - 分钟（如：28）
{SS} - 秒钟（如：09）

示例：
{YYYY}{MM}{DD}_{HH}{mm}{SS} → 20250415_122809.jpg
IMG-{YYYY}{MM}{DD}_{HH}{mm}{SS} → IMGS-20250415_122809.jpg
Photo_{YYYY}-{MM}-{DD} → Photo_2025-04-15.jpg

注意：
- 变量必须用花括号 {} 包裹
- 其他文本将保持原样
- 例如：MyPhoto_{YYYY} → MyPhoto_2025.jpg
        """
        help_btn.setToolTip(help_text)
        help_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                color: #666666;
                font-size: 16px;
                font-weight: normal;
                padding: 0px;
                font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", "Microsoft YaHei", sans-serif;
                min-width: 32px;
                max-width: 32px;
            }
            QPushButton:hover {
                background: #f5f5f5;
                color: #FFC107;
                border-color: #FFC107;
            }
            QToolTip {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                max-width: 400px;
            }
        """)
        
        def show_help():
            QToolTip.showText(help_btn.mapToGlobal(help_btn.rect().bottomRight()), help_text, help_btn)
        
        help_btn.clicked.connect(show_help)
        template_input_layout.addWidget(help_btn)
        template_input_layout.addStretch()
        
        template_layout.addLayout(template_input_layout)
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)

        source_group = QGroupBox("日期来源")
        source_layout = QVBoxLayout()
        source_layout.setSpacing(16)
        source_layout.setContentsMargins(16, 20, 16, 16)
        
        primary_layout = QHBoxLayout()
        primary_layout.setSpacing(12)
        primary_label = QLabel("首选日期来源")
        primary_label.setStyleSheet("color: #666666; font-size: 13px;")
        primary_label.setFixedWidth(100)
        primary_layout.addWidget(primary_label)
        
        self.date_source = QComboBox()
        self.date_source.addItems(["拍摄日期", "修改日期", "创建日期", "当前日期"])
        self.date_source.setCurrentText(self.settings.get("date_source", "拍摄日期"))
        self.date_source.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                min-width: 200px;
                height: 32px;
            }
            QComboBox:hover {
                border-color: #999999;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
        """)
        primary_layout.addWidget(self.date_source)
        primary_layout.addStretch()
        source_layout.addLayout(primary_layout)
        
        fallback_layout = QHBoxLayout()
        fallback_layout.setSpacing(12)
        fallback_label = QLabel("备选日期来源")
        fallback_label.setStyleSheet("color: #666666; font-size: 13px;")
        fallback_label.setFixedWidth(100)
        fallback_layout.addWidget(fallback_label)
        
        self.fallback_date_source = QComboBox()
        self.fallback_date_source.addItems(["修改日期", "创建日期", "当前日期"])
        self.fallback_date_source.setCurrentText(self.settings.get("fallback_date_source", "修改日期"))
        self.fallback_date_source.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                min-width: 200px;
                height: 32px;
            }
            QComboBox:hover {
                border-color: #999999;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
        """)
        fallback_layout.addWidget(self.fallback_date_source)
        fallback_layout.addStretch()
        source_layout.addLayout(fallback_layout)

        non_media_layout = QHBoxLayout()
        non_media_layout.setSpacing(12)
        self.enable_non_media = QCheckBox("非媒体文件日期来源")
        self.enable_non_media.setChecked(self.settings.get("enable_non_media", True))
        self.enable_non_media.setStyleSheet("""
            QCheckBox {
                color: #666666;
                font-size: 13px;
                padding: 4px 0;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QCheckBox::indicator:hover {
                border-color: #999999;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
        """)
        non_media_layout.addWidget(self.enable_non_media)
        
        self.non_media_date_source = QComboBox()
        self.non_media_date_source.addItems(["创建日期", "修改日期", "当前日期"])
        self.non_media_date_source.setCurrentText(self.settings.get("non_media_date_source", "创建日期"))
        self.non_media_date_source.setEnabled(self.enable_non_media.isChecked())
        self.enable_non_media.toggled.connect(self.non_media_date_source.setEnabled)
        self.non_media_date_source.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                min-width: 200px;
                height: 32px;
            }
            QComboBox:hover {
                border-color: #999999;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
            QComboBox:disabled {
                background: #f5f5f5;
                color: #999999;
            }
        """)
        non_media_layout.addWidget(self.non_media_date_source)
        non_media_layout.addStretch()
        source_layout.addLayout(non_media_layout)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        handling_group = QGroupBox("重名处理")
        handling_layout = QHBoxLayout()
        handling_layout.setSpacing(20)
        handling_layout.setContentsMargins(16, 20, 16, 16)
        
        self.duplicate_handling = QButtonGroup(self)
        self.keep_original_radio = QRadioButton("保留原名称")
        self.add_suffix_radio = QRadioButton("增加序号后缀")
        radio_style = """
            QRadioButton {
                color: #666666;
                font-size: 13px;
                padding: 4px 0;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #e0e0e0;
                border-radius: 9px;
            }
            QRadioButton::indicator:hover {
                border-color: #999999;
            }
            QRadioButton::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
        """
        self.keep_original_radio.setStyleSheet(radio_style)
        self.add_suffix_radio.setStyleSheet(radio_style)
        self.duplicate_handling.addButton(self.keep_original_radio)
        self.duplicate_handling.addButton(self.add_suffix_radio)
        
        if self.settings.get("duplicate_handling", "add_suffix") == "keep_original":
            self.keep_original_radio.setChecked(True)
        else:
            self.add_suffix_radio.setChecked(True)
            
        handling_layout.addWidget(self.keep_original_radio)
        handling_layout.addWidget(self.add_suffix_radio)
        handling_layout.addStretch()
        
        handling_group.setLayout(handling_layout)
        layout.addWidget(handling_group)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 100px;
                height: 36px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #1565C0;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.save_btn)
        
        self.back_btn = QPushButton("返回")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #666666;
                border: 1px solid #e0e0e0;
                padding: 8px 24px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 100px;
                height: 36px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
            QPushButton:pressed {
                background: #d0d0d0;
            }
        """)
        self.back_btn.clicked.connect(self.return_to_main)
        btn_layout.addWidget(self.back_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        template = self.settings.get("name_template", "{YYYY}{MM}{DD}_{HH}{mm}{SS}")
        self.custom_format.setText(template)

    def load_settings(self):
        default_settings = {
            "date_source": "拍摄日期",
            "fallback_date_source": "修改日期",
            "duplicate_handling": "add_suffix",
            "name_template": "{YYYY}{MM}{DD}_{HH}{mm}{SS}",
            "custom_format": "{YYYY}{MM}{DD}_{HH}{mm}{SS}",
            "enable_non_media": True,
            "non_media_date_source": "创建日期"
        }
        
        config_path = get_config_file_path()
        try:
            if not os.path.exists(config_path):
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(default_settings, f, ensure_ascii=False, indent=4)
                return default_settings
            
            with open(config_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            return settings
        except Exception:
            return default_settings

    def save_settings(self):
        dup_handle = "keep_original" if self.keep_original_radio.isChecked() else "add_suffix"
        self.settings = {
            "date_source": self.date_source.currentText(),
            "fallback_date_source": self.fallback_date_source.currentText(),
            "name_template": self.custom_format.text() or "{YYYY}{MM}{DD}_{HH}{mm}{SS}",
            "custom_format": self.custom_format.text() or "{YYYY}{MM}{DD}_{HH}{mm}{SS}",
            "enable_non_media": self.enable_non_media.isChecked(),
            "non_media_date_source": self.non_media_date_source.currentText(),
            "duplicate_handling": dup_handle
        }
        try:
            config_path = get_config_file_path()
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            if isinstance(self.parent, MainWindow):
                self.parent.settings = self.settings
            self.return_to_main()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置失败: {str(e)}")

    def return_to_main(self):
        if isinstance(self.parent, MainWindow):
            self.parent.stacked_layout.setCurrentWidget(self.parent.main_panel)


class RenameWorker(QThread):
    # progress 发送：(索引, 原完整路径, 新完整路径, 状态信息, 是否成功)
    progress = pyqtSignal(int, str, str, str, bool)
    finished = pyqtSignal(int)

    def __init__(self, files, settings):
        super().__init__()
        self.files = files.copy()
        self.settings = settings
        self.success_count = 0
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        processed_files = set()
        occupied_paths = {os.path.normcase(os.path.abspath(f)) for f in self.files if os.path.exists(f)}
        
        for idx, file_path in enumerate(self.files):
            if not self._is_running:
                break

            try:
                if file_path in processed_files or not os.path.exists(file_path):
                    continue

                if self.settings.get("date_source") == "当前日期":
                    date = datetime.now()
                else:
                    date = self.get_file_date(file_path)

                base_name = self.get_base_filename(date)
                ext = os.path.splitext(file_path)[1]
                new_name = f"{base_name}{ext}"
                
                dir_path = os.path.dirname(file_path)
                new_path = os.path.join(dir_path, new_name)

                # 原名已匹配
                if os.path.basename(file_path) == new_name:
                    self.progress.emit(idx, file_path, file_path, "已符合命名格式", False)
                    processed_files.add(file_path)
                    continue

                norm_src = os.path.normcase(os.path.abspath(file_path))
                norm_dst = os.path.normcase(os.path.abspath(new_path))
                is_same_file_diff_case = (norm_src == norm_dst)

                # 冲突检测：目标文件已存在或属于本次重命名批次中其他文件
                conflict = (os.path.exists(new_path) or norm_dst in occupied_paths) and not is_same_file_diff_case
                if conflict:
                    if self.settings.get("duplicate_handling", "add_suffix") == "keep_original":
                        self.progress.emit(idx, file_path, file_path, "跳过: 文件已存在", False)
                        processed_files.add(file_path)
                        continue
                    else:
                        count = 1
                        found_unique = False
                        while count < 10000:
                            candidate_name = f"{base_name}_{count:03d}{ext}"
                            candidate_path = os.path.join(dir_path, candidate_name)
                            cand_norm = os.path.normcase(os.path.abspath(candidate_path))
                            if not os.path.exists(candidate_path) and cand_norm not in occupied_paths:
                                new_name = candidate_name
                                new_path = candidate_path
                                norm_dst = cand_norm
                                found_unique = True
                                break
                            count += 1
                        
                        if not found_unique:
                            self.progress.emit(idx, file_path, file_path, "错误: 无法找到可用的文件名", False)
                            processed_files.add(file_path)
                            continue

                # 执行重命名
                try:
                    if is_same_file_diff_case and os.name == 'nt':
                        temp_path = os.path.join(dir_path, f"__tmp_{datetime.now().timestamp()}_{ext}")
                        os.rename(file_path, temp_path)
                        os.rename(temp_path, new_path)
                    else:
                        if os.path.exists(new_path) and not is_same_file_diff_case:
                            self.progress.emit(idx, file_path, file_path, "跳过: 目标文件已存在", False)
                            processed_files.add(file_path)
                            continue
                        os.rename(file_path, new_path)

                    occupied_paths.discard(norm_src)
                    occupied_paths.add(norm_dst)
                    
                    self.success_count += 1
                    processed_files.add(file_path)
                    self.progress.emit(idx, file_path, new_path, new_name, True)

                except PermissionError:
                    self.progress.emit(idx, file_path, file_path, "错误: 文件被占用或无权限", False)
                    processed_files.add(file_path)
                except OSError as e:
                    self.progress.emit(idx, file_path, file_path, f"错误: {str(e)}", False)
                    processed_files.add(file_path)

            except Exception as e:
                self.progress.emit(idx, file_path, file_path, f"错误: {str(e)}", False)
                processed_files.add(file_path)

        self.finished.emit(self.success_count)

    def get_base_filename(self, date):
        template = self.settings.get("name_template", "{YYYY}{MM}{DD}_{HH}{mm}{SS}")
        try:
            format_str = template
            format_str = format_str.replace("{YYYY}", date.strftime("%Y"))
            format_str = format_str.replace("{MM}", date.strftime("%m"))
            format_str = format_str.replace("{DD}", date.strftime("%d"))
            format_str = format_str.replace("{HH}", date.strftime("%H"))
            format_str = format_str.replace("{mm}", date.strftime("%M"))
            format_str = format_str.replace("{SS}", date.strftime("%S"))
            return format_str
        except Exception:
            return date.strftime("%Y%m%d_%H%M%S")

    def get_file_date(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic', '.heif', 
            '.tiff', '.tif', '.webp', '.raw', '.arw', '.cr2', '.nef', 
            '.dng', '.orf', '.sr2', '.rw2'
        }
        
        # 仅对支持的静态图片提取 EXIF
        if ext in image_extensions and self.settings.get("date_source") == "拍摄日期":
            try:
                with open(file_path, 'rb') as f:
                    exif_data = exif.Image(f)
                    if exif_data.has_exif:
                        date_str = None
                        for field in ['datetime_original', 'datetime']:
                            if hasattr(exif_data, field):
                                date_str = getattr(exif_data, field)
                                break
                        if date_str:
                            for fmt in ["%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                                try:
                                    return datetime.strptime(str(date_str), fmt)
                                except ValueError:
                                    continue
            except Exception:
                pass

        try:
            stat = os.stat(file_path)
            fallback_source = self.settings.get("fallback_date_source", "修改日期")
            if fallback_source == "修改日期":
                return datetime.fromtimestamp(stat.st_mtime)
            elif fallback_source == "创建日期":
                return datetime.fromtimestamp(stat.st_ctime)
        except Exception:
            pass

        return datetime.now()


class FileTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        row = self.rowAt(pos.y())
        if row >= 0:
            delete_action = QAction("从列表中移除", self)
            delete_action.triggered.connect(lambda: self.remove_file(row))
            menu.addAction(delete_action)
            menu.addSeparator()
        
        clear_action = QAction("清空列表", self)
        clear_action.triggered.connect(self.clear_all)
        menu.addAction(clear_action)
        menu.exec_(self.mapToGlobal(pos))

    def remove_file(self, row):
        if isinstance(self.parent, MainWindow):
            if 0 <= row < len(self.parent.files):
                self.parent.files.pop(row)
            self.removeRow(row)
            self.parent.update_list_button_text()

    def clear_all(self):
        if isinstance(self.parent, MainWindow):
            self.parent.clear_files()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__app_name__} {__version__} —— {__author__}")
        
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 80px;
                min-height: 36px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #1565C0;
            }
            QPushButton:disabled {
                background: #BDBDBD;
                color: #E0E0E0;
            }
            QPushButton#renameButton {
                background: #F44336;
            }
            QPushButton#renameButton:hover {
                background: #D32F2F;
            }
            QPushButton#renameButton:pressed {
                background: #B71C1C;
            }
            QPushButton#renameButton:disabled {
                background: #BDBDBD;
                color: #E0E0E0;
            }
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                font-size: 13px;
                gridline-color: #f5f5f5;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f5f5f5;
            }
            QTableWidget::item:selected {
                background-color: #e8f0fe;
                color: #1a73e8;
                outline: none;
            }
            QTableWidget::item:focus {
                outline: none;
                border: none;
            }
            QHeaderView::section {
                background-color: #f8f8f8;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
            }
            QStatusBar {
                background-color: #f5f5f5;
                color: #666666;
                border-top: 1px solid #e0e0e0;
                padding: 5px;
            }
            QStatusBar QLabel {
                color: #666666;
                font-size: 14px;
                padding: 5px;
                border-radius: 4px;
            }
            QStatusBar QLabel:hover {
                background-color: #e8e8e8;
            }
            #closeButton {
                background: none;
                border: none;
                color: #999999;
                font-size: 16px;
                padding: 5px;
                border-radius: 4px;
            }
            #closeButton:hover {
                background-color: #f0f0f0;
                color: #666666;
            }
            QMenu {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #e8f0fe;
                color: #1a73e8;
            }
        """)
        self.files = []
        self.settings = SettingsPanel.load_settings(self)
        self.has_renamed = False
        self.current_success_count = 0
        self.init_ui()
        self.setup_animations()

    def setup_animations(self):
        self.start_animation = QPropertyAnimation(self.action_btn, b"geometry")
        self.start_animation.setDuration(150)
        self.start_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.settings_animation = QPropertyAnimation(self.settings_btn, b"geometry")
        self.settings_animation.setDuration(150)
        self.settings_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.toggle_animation = QPropertyAnimation(self.toggle_list_btn, b"geometry")
        self.toggle_animation.setDuration(150)
        self.toggle_animation.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        if self.action_btn.underMouse():
            self.animate_button(self.action_btn, self.start_animation, True)
        elif self.settings_btn.underMouse():
            self.animate_button(self.settings_btn, self.settings_animation, True)
        elif self.toggle_list_btn.underMouse():
            self.animate_button(self.toggle_list_btn, self.toggle_animation, True)

    def leaveEvent(self, event):
        if self.action_btn.underMouse():
            self.animate_button(self.action_btn, self.start_animation, False)
        elif self.settings_btn.underMouse():
            self.animate_button(self.settings_btn, self.settings_animation, False)
        elif self.toggle_list_btn.underMouse():
            self.animate_button(self.toggle_list_btn, self.toggle_animation, False)

    def animate_button(self, button, animation, is_enter):
        current_geometry = button.geometry()
        if is_enter:
            animation.setStartValue(current_geometry)
            animation.setEndValue(current_geometry.adjusted(0, -2, 0, -2))
        else:
            animation.setStartValue(current_geometry)
            animation.setEndValue(current_geometry.adjusted(0, 2, 0, 2))
        animation.start()

    def init_ui(self):
        self.setMinimumSize(500, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_layout = QStackedLayout(central_widget)

        self.main_panel = QWidget()
        layout = QVBoxLayout(self.main_panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.drop_area = DropArea(self)
        self.drop_area.setMinimumHeight(200)
        layout.addWidget(self.drop_area)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        self.file_list = FileTableWidget(self)
        self.file_list.setColumnCount(2)
        self.file_list.setHorizontalHeaderLabels(["文件名", "状态"])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.file_list.setColumnWidth(1, 60)
        self.file_list.setMinimumHeight(200)
        self.file_list.setVisible(False)
        self.file_list.setShowGrid(False)
        self.file_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_list.verticalHeader().setVisible(False)
        self.file_list.horizontalHeaderItem(0).setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.file_list.horizontalHeaderItem(1).setTextAlignment(Qt.AlignCenter)
        self.file_list.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.file_list.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        list_layout.addWidget(self.file_list)
        
        list_container.hide()
        layout.addWidget(list_container)
        self.list_container = list_container

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 10, 0, 0)

        self.toggle_list_btn = AnimatedButton("▼")
        self.toggle_list_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #f0f0f0, stop:1 #e8e8e8);
                color: #333333;
                border: 1px solid #e0e0e0;
                padding: 8px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 32px;
                max-width: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #e8e8e8, stop:1 #d8d8d8);
                border-color: #d0d0d0;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #d8d8d8, stop:1 #c8c8c8);
            }
        """)
        self.toggle_list_btn.clicked.connect(self.toggle_file_list)
        button_layout.addWidget(self.toggle_list_btn)
        
        self.action_btn = AnimatedButton("开始")
        self.action_btn.setObjectName("actionButton")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 80px;
                min-height: 36px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #1565C0;
            }
            QPushButton:disabled {
                background: #BDBDBD;
                color: #E0E0E0;
            }
        """)
        self.action_btn.clicked.connect(self.toggle_action)
        button_layout.addWidget(self.action_btn)
        
        self.settings_btn = AnimatedButton("⚙")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #f0f0f0, stop:1 #e8e8e8);
                color: #333333;
                border: 1px solid #e0e0e0;
                padding: 8px;
                border-radius: 6px;
                font-size: 16px;
                min-width: 32px;
                max-width: 32px;
                font-family: "Segoe UI Symbol", "Arial Unicode MS", "Microsoft YaHei";
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #e8e8e8, stop:1 #d8d8d8);
                border-color: #d0d0d0;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #d8d8d8, stop:1 #c8c8c8);
            }
        """)
        self.settings_btn.clicked.connect(self.show_settings)
        button_layout.addWidget(self.settings_btn)
        
        layout.addLayout(button_layout)
        self.stacked_layout.addWidget(self.main_panel)

        self.settings_panel = SettingsPanel(self)
        self.settings_panel.back_btn.clicked.connect(self.show_main_panel)
        self.stacked_layout.addWidget(self.settings_panel)
        self.stacked_layout.setCurrentWidget(self.main_panel)

        self.statusBar = self.statusBar()
        self.status_label = QLabel("")
        self.statusBar.addWidget(self.status_label)

    def toggle_file_list(self):
        if self.list_container.isVisible():
            self.hide_file_list()
        else:
            self.show_file_list()

    def show_file_list(self, event=None):
        if not self.list_container.isVisible():
            self.list_container.show()
            self.file_list.setVisible(True)
            self.toggle_list_btn.setText("▲")
            self.update_list_button_text()
            if self.file_list.rowCount() > 0:
                self.file_list.scrollToBottom()

    def hide_file_list(self):
        self.list_container.hide()
        self.file_list.setVisible(False)
        self.toggle_list_btn.setText("▼")
        self.update_list_button_text()

    def show_message(self, message, duration=3000):
        if duration == 0 and "正在重命名" in self.status_label.text():
            return
        self.status_label.setText(message)
        if duration > 0:
            QTimer.singleShot(duration, self.update_list_button_text)

    def update_list_button_text(self):
        if not self.files:
            self.status_label.setText("")
            return

        latest_file = self.files[-1]
        file_name = os.path.basename(latest_file)
        if len(self.files) == 1:
            self.status_label.setText(file_name)
        else:
            self.status_label.setText(f"共{len(self.files)}个文件")
            if len(self.status_label.text()) > 50:
                self.status_label.setText(f"共{len(self.files)}个文件 - {file_name[:30]}...")

    def add_files(self, files):
        if self.has_renamed:
            self.clear_files()
            self.has_renamed = False

        existing_files = set(self.files)
        files_to_add = [f for f in files if f not in existing_files]
        if not files_to_add:
            return

        self.file_list.setUpdatesEnabled(False)
        current_rows = self.file_list.rowCount()
        self.file_list.setRowCount(current_rows + len(files_to_add))
        
        for idx, file_path in enumerate(files_to_add):
            row = current_rows + idx
            self.files.append(file_path)
            
            name_item = QTableWidgetItem(os.path.basename(file_path))
            status_item = QTableWidgetItem("●")
            status_item.setTextAlignment(Qt.AlignCenter)
            
            self.file_list.setItem(row, 0, name_item)
            self.file_list.setItem(row, 1, status_item)

        self.file_list.setUpdatesEnabled(True)
        if self.file_list.isVisible():
            self.file_list.scrollToBottom()
        self.update_list_button_text()

    def show_settings(self):
        self.stacked_layout.setCurrentWidget(self.settings_panel)

    def show_main_panel(self):
        self.stacked_layout.setCurrentWidget(self.main_panel)

    def toggle_action(self):
        if self.action_btn.text().startswith("开始"):
            if not self.files:
                self.show_message("请先添加文件", 2000)
                return
            self.start_rename()
            self.action_btn.setText("停止")
            self.action_btn.setObjectName("renameButton")
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background: #F44336;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 14px;
                    min-width: 80px;
                    min-height: 36px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #D32F2F;
                }
                QPushButton:pressed {
                    background: #B71C1C;
                }
            """)
        else:
            self.stop_rename()

    def start_rename(self):
        if not self.files:
            return
        if not self.list_container.isVisible():
            self.show_file_list()
        
        self.current_success_count = 0
        self.worker = RenameWorker(self.files, self.settings)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.rename_finished)
        self.worker.start()
        self.show_message("正在重命名文件...", 0)

    def stop_rename(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.action_btn.setEnabled(False)
            self.worker.stop()
            self.worker.wait()
            self.action_btn.setEnabled(True)

    def update_progress(self, index, old_path, new_path, status_text, is_success):
        if 0 <= index < self.file_list.rowCount():
            if is_success:
                self.files[index] = new_path
                self.file_list.item(index, 0).setText(os.path.basename(new_path))
                self.file_list.item(index, 1).setText("✓")
                self.file_list.item(index, 1).setForeground(QColor("#4CAF50"))
                self.current_success_count += 1
                
                total = len(self.files)
                self.show_message(f"正在重命名... ({self.current_success_count}/{total})", 0)
                self.action_btn.setText(f"停止 ({self.current_success_count}/{total})")
            else:
                if "错误" in status_text:
                    self.file_list.item(index, 1).setText("✗")
                    self.file_list.item(index, 1).setForeground(QColor("#F44336"))
                elif "已符合命名格式" in status_text:
                    self.file_list.item(index, 1).setText("✓")
                    self.file_list.item(index, 1).setForeground(QColor("#4CAF50"))
                else:
                    self.file_list.item(index, 1).setText("○")
                    self.file_list.item(index, 1).setForeground(QColor("#9E9E9E"))

    def rename_finished(self, success_count):
        self.action_btn.setText("开始")
        self.action_btn.setObjectName("actionButton")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 80px;
                min-height: 36px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #1565C0;
            }
            QPushButton:disabled {
                background: #BDBDBD;
                color: #E0E0E0;
            }
        """)
        if success_count > 0:
            self.status_label.setText("")
            QTimer.singleShot(100, lambda: self.show_message(f"✓ 已重命名 {success_count} 个文件", 3000))
            self.drop_area.show_success(success_count)
            self.has_renamed = True
        else:
            self.show_message("没有文件被重命名", 3000)
            self.update_list_button_text()

    def clear_files(self):
        self.files.clear()
        self.file_list.setRowCount(0)
        self.drop_area.label.setText("拖放文件或文件夹到这里\n或点击选择文件")
        self.status_label.setText("")
        self.list_container.hide()
        self.has_renamed = False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    icon_path = get_resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    app.setStyle("Fusion")
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
