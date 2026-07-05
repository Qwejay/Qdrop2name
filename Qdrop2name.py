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
__version__ = "1.1"
__author__ = "QwejayHuang"
__company__ = "QwejayHuang"
__description__ = "文件智能重命名工具"


register_heif_opener()

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
        
        # 添加图标和提示文本
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
                files.append(path)
            elif os.path.isdir(path):
                files.extend(self.get_files_from_dir(path))
        if files:
            main_window = self.window()
            if isinstance(main_window, MainWindow):
                main_window.add_files(files)
                # 更新显示的文件数量
                total_files = len(main_window.files)
                self.label.setText(f"已选择 {total_files} 个文件")

    def get_files_from_dir(self, dir_path):
        """递归获取文件夹中的所有支持的文件"""
        files = []
        for root, _, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if self.is_supported_file(file_path):
                    files.append(file_path)
        return files

    def is_supported_file(self, file_path):
        """检查文件是否为支持的类型"""
        try:
            # 检查文件是否存在或可访问
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
            # 通过主窗口访问settings
            main_window = self.window()
            if hasattr(main_window, 'settings') and main_window.settings.get("enable_non_media", False):
                return True
            return ext in image_extensions or ext in video_extensions
        except Exception as e:
            print(f"文件检查错误: {str(e)}")
            return False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:  
            self.open_file_dialog()

    def open_file_dialog(self):
        dialog = QFileDialog()
        dialog.setWindowTitle("选择文件")
        dialog.setFileMode(QFileDialog.ExistingFiles)
        
        # 设置文件过滤器
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
        
        if dialog.exec_():  # ← PyQt5 使用 exec_()
            files = []
            for path in dialog.selectedFiles():
                if os.path.isfile(path):
                    files.append(path)
                elif os.path.isdir(path):
                    files.extend(self.get_files_from_dir(path))
            
            if files:
                main_window = self.window()
                if isinstance(main_window, MainWindow):
                    main_window.add_files(files)
                    # 更新显示的文件数量
                    total_files = len(main_window.files)
                    self.label.setText(f"已选择 {total_files} 个文件")

    def show_success(self, count):
        """显示成功提示"""
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
        # 3秒后恢复原始文本
        QTimer.singleShot(3000, self.reset_label)

    def reset_label(self):
        """恢复原始文本"""
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
        
        # 创建动画组
        self.animation_group = QParallelAnimationGroup()
        
        # 创建位置动画
        self.position_animation = QPropertyAnimation(self, b"geometry")
        self.position_animation.setDuration(150)
        self.position_animation.setEasingCurve(QEasingCurve.OutCubic)  # ← PyQt5
        
        # 创建透明度动画
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(200)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutCubic)  # ← PyQt5
        
        # 将动画添加到动画组
        self.animation_group.addAnimation(self.position_animation)
        self.animation_group.addAnimation(self.opacity_animation)
        
        # 设置初始状态
        self.is_hovered = False

    def enterEvent(self, event):
        if not self.is_hovered:
            self.is_hovered = True
            # 设置位置动画
            current_geometry = self.geometry()
            self.position_animation.setStartValue(current_geometry)
            self.position_animation.setEndValue(current_geometry.adjusted(0, -2, 0, -2))
            
            # 设置透明度动画
            self.opacity_animation.setStartValue(1.0)
            self.opacity_animation.setEndValue(0.8)
            
            # 启动动画组
            self.animation_group.start()

    def leaveEvent(self, event):
        if self.is_hovered:
            self.is_hovered = False
            # 设置位置动画
            current_geometry = self.geometry()
            self.position_animation.setStartValue(current_geometry)
            self.position_animation.setEndValue(current_geometry.adjusted(0, 2, 0, 2))
            
            # 设置透明度动画
            self.opacity_animation.setStartValue(0.8)
            self.opacity_animation.setEndValue(1.0)
            
            # 启动动画组
            self.animation_group.start()

# 新建设置面板
class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.settings = self.load_settings()  # 初始化settings属性
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
        layout.setSpacing(24)  # 增加组之间的间距
        layout.setContentsMargins(30, 30, 30, 30)

        # 命名模板组
        template_group = QGroupBox("命名模板")
        template_layout = QVBoxLayout()
        template_layout.setSpacing(16)  # 增加元素之间的间距
        template_layout.setContentsMargins(16, 20, 16, 16)  # 调整内边距
        
        # 模板输入区域
        template_input_layout = QHBoxLayout()
        template_input_layout.setSpacing(12)  # 调整水平间距
        
        # 自定义格式输入
        self.custom_format_label = QLabel("命名模板")
        self.custom_format_label.setStyleSheet("color: #666666; font-size: 13px;")
        self.custom_format_label.setFixedWidth(80)  # 固定标签宽度
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
        
        # 添加帮助按钮
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
        
        # 添加点击事件处理
        def show_help():
            QToolTip.showText(help_btn.mapToGlobal(help_btn.rect().bottomRight()), help_text, help_btn)
        
        help_btn.clicked.connect(show_help)
        template_input_layout.addWidget(help_btn)
        template_input_layout.addStretch()
        
        template_layout.addLayout(template_input_layout)
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)

        # 日期来源组
        source_group = QGroupBox("日期来源")
        source_layout = QVBoxLayout()
        source_layout.setSpacing(16)  # 增加元素之间的间距
        source_layout.setContentsMargins(16, 20, 16, 16)  # 调整内边距
        
        # 首选日期来源
        primary_layout = QHBoxLayout()
        primary_layout.setSpacing(12)  # 调整水平间距
        primary_label = QLabel("首选日期来源")
        primary_label.setStyleSheet("color: #666666; font-size: 13px;")
        primary_label.setFixedWidth(100)  # 固定标签宽度
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
        
        # 备选日期来源
        fallback_layout = QHBoxLayout()
        fallback_layout.setSpacing(12)  # 调整水平间距
        fallback_label = QLabel("备选日期来源")
        fallback_label.setStyleSheet("color: #666666; font-size: 13px;")
        fallback_label.setFixedWidth(100)  # 固定标签宽度
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

        # 非媒体文件选项
        non_media_layout = QHBoxLayout()
        non_media_layout.setSpacing(12)  # 调整水平间距
        self.enable_non_media = QCheckBox("非媒体文件日期来源")
        self.enable_non_media.setChecked(self.settings.get("enable_non_media", False))
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

        # 重名处理组
        handling_group = QGroupBox("重名处理")
        handling_layout = QHBoxLayout()
        handling_layout.setSpacing(20)
        handling_layout.setContentsMargins(16, 20, 16, 16)  # 调整内边距
        
        self.duplicate_handling = QButtonGroup(self)
        keep_original = QRadioButton("保留原名称")
        add_suffix = QRadioButton("增加序号后缀")
        keep_original.setStyleSheet("""
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
        """)
        add_suffix.setStyleSheet("""
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
        """)
        self.duplicate_handling.addButton(keep_original)
        self.duplicate_handling.addButton(add_suffix)
        if self.settings.get("duplicate_handling", "add_suffix") == "keep_original":
            keep_original.setChecked(True)
        else:
            add_suffix.setChecked(True)
        handling_layout.addWidget(keep_original)
        handling_layout.addWidget(add_suffix)
        handling_layout.addStretch()
        
        handling_group.setLayout(handling_layout)
        layout.addWidget(handling_group)

        # 按钮区域
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
        
        # 设置初始模板
        template = self.settings.get("name_template", "YYYYMMDD_HHMMSS_001")
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
        
        try:
            # 检查配置文件是否存在
            if not os.path.exists("settings.json"):
                # 如果不存在，创建默认配置文件
                with open("settings.json", "w", encoding="utf-8") as f:
                    json.dump(default_settings, f, ensure_ascii=False, indent=4)
                return default_settings
            
            # 读取现有配置
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # 检查必要的键是否存在，如果不存在则使用默认值
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            
            return settings
        except Exception as e:
            print(f"加载设置错误: {str(e)}")
            # 发生任何错误，返回默认设置
            return default_settings

    def save_settings(self):
        self.settings = {
            "date_source": self.date_source.currentText(),
            "fallback_date_source": self.fallback_date_source.currentText(),
            "name_template": self.custom_format.text(),
            "custom_format": self.custom_format.text(),
            "enable_non_media": self.enable_non_media.isChecked(),
            "non_media_date_source": self.non_media_date_source.currentText()
        }
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
                # 更新主窗口的设置
                if isinstance(self.parent, MainWindow):
                    self.parent.settings = self.settings
            self.return_to_main()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置失败: {str(e)}")

    def return_to_main(self):
        if isinstance(self.parent, MainWindow):
            self.parent.stacked_layout.setCurrentWidget(self.parent.main_panel)

class RenameWorker(QThread):
    progress = pyqtSignal(str, str)
    finished = pyqtSignal(int)

    def __init__(self, files, settings):
        super().__init__()
        self.files = files.copy()
        self.settings = settings
        self.success_count = 0

    def run(self):
        # 用于跟踪每个时间戳对应的文件数量
        timestamp_counter = {}
        processed_files = set()
        
        for file_path in self.files:
            try:
                if file_path in processed_files:
                    continue
                    
                # 获取日期信息
                if self.settings["date_source"] == "当前日期":
                    date = datetime.now()
                else:
                    date = self.get_file_date(file_path)
                
                # 生成基础文件名（不含序号）
                base_name = self.get_base_filename(date)
                ext = os.path.splitext(file_path)[1].lower()
                
                # 获取当前时间戳对应的计数
                timestamp = date.strftime("%Y%m%d_%H%M%S")
                if timestamp not in timestamp_counter:
                    timestamp_counter[timestamp] = 0
                timestamp_counter[timestamp] += 1
                
                # 生成新文件名
                new_name = f"{base_name}{ext}"
                
                dir_path = os.path.dirname(file_path)
                new_path = os.path.join(dir_path, new_name)

                # 获取当前文件名（不含路径）
                current_name = os.path.basename(file_path)
                
                # 检查文件名是否已经是预期格式
                if current_name == new_name:
                    self.progress.emit(file_path, "已符合命名格式")
                    processed_files.add(file_path)
                    continue

                # 跳过目标文件名和源文件名完全一致的情况
                if os.path.abspath(file_path) == os.path.abspath(new_path):
                    self.progress.emit(file_path, "跳过: 文件名未变化")
                    processed_files.add(file_path)
                    continue

                # 处理重名文件
                if os.path.exists(new_path) and os.path.abspath(file_path) != os.path.abspath(new_path):
                    if self.settings.get("duplicate_handling", "keep_original") == "keep_original":
                        # 如果选择保留原名称，则跳过重命名
                        self.progress.emit(file_path, "跳过: 文件已存在")
                        processed_files.add(file_path)
                        continue
                    else:  # add_suffix
                        # 如果选择增加序号后缀，则查找下一个可用的序号
                        base_name_without_ext, ext = os.path.splitext(new_name)
                        count = 1
                        max_attempts = 1000  # 防止无限循环
                        while count < max_attempts:
                            candidate_name = f"{base_name_without_ext}_{count:03d}{ext}"
                            candidate_path = os.path.join(dir_path, candidate_name)
                            if not os.path.exists(candidate_path) or os.path.abspath(candidate_path) == os.path.abspath(file_path):
                                new_name = candidate_name
                                new_path = candidate_path
                                break
                            count += 1
                        
                        if count >= max_attempts:
                            self.progress.emit(file_path, "错误: 无法找到可用的文件名")
                            processed_files.add(file_path)
                            continue

                # 检查文件是否可写
                try:
                    if not os.access(dir_path, os.W_OK):
                        self.progress.emit(file_path, "错误: 没有写入权限")
                        processed_files.add(file_path)
                        continue
                    
                    # 临时检查文件是否被占用
                    try:
                        with open(file_path, "a"):
                            pass
                    except IOError:
                        self.progress.emit(file_path, "错误: 文件被占用")
                        processed_files.add(file_path)
                        continue
                except Exception as e:
                    self.progress.emit(file_path, f"错误: 权限检查失败 - {str(e)}")
                    processed_files.add(file_path)
                    continue

                # 执行重命名
                try:
                    os.rename(file_path, new_path)
                    self.progress.emit(file_path, new_path)
                    self.success_count += 1
                    processed_files.add(file_path)
                    # 更新文件列表中的路径
                    for i, f in enumerate(self.files):
                        if f == file_path:
                            self.files[i] = new_path
                            break
                except PermissionError:
                    self.progress.emit(file_path, "错误: 没有足够的权限")
                    processed_files.add(file_path)
                except OSError as e:
                    self.progress.emit(file_path, f"错误: {str(e)}")
                    processed_files.add(file_path)
            except Exception as e:
                self.progress.emit(file_path, f"错误: {str(e)}")
                processed_files.add(file_path)
        self.finished.emit(self.success_count)

    def get_base_filename(self, date):
        """根据日期和模板生成基础文件名（不含序号）"""
        template = self.settings["name_template"]
        # 直接使用自定义格式
        try:
            # 替换所有可能的日期时间格式
            format_str = template
            format_str = format_str.replace("{YYYY}", date.strftime("%Y"))
            format_str = format_str.replace("{MM}", date.strftime("%m"))
            format_str = format_str.replace("{DD}", date.strftime("%d"))
            format_str = format_str.replace("{HH}", date.strftime("%H"))
            format_str = format_str.replace("{mm}", date.strftime("%M"))
            format_str = format_str.replace("{SS}", date.strftime("%S"))
            
            # 返回替换后的结果
            return format_str
        except Exception as e:
            # 出错时回退到安全格式
            print(f"格式解析错误: {str(e)}")
            return date.strftime("%Y%m%d_%H%M%S")

    def get_file_date(self, file_path):
        # 检查是否为非媒体文件
        ext = os.path.splitext(file_path)[1].lower()
        is_media_file = ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic', '.heif',
                              '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        
        # 如果是非媒体文件且启用了非媒体文件支持
        if not is_media_file and self.settings.get("enable_non_media", False):
            stat = os.stat(file_path)
            date_source = self.settings.get("non_media_date_source", "创建日期")
            if date_source == "创建日期":
                return datetime.fromtimestamp(stat.st_ctime)
            elif date_source == "修改日期":
                return datetime.fromtimestamp(stat.st_mtime)
            else:  # 当前日期
                return datetime.now()

        # 尝试获取首选日期
        if self.settings["date_source"] == "拍摄日期":
            try:
                with open(file_path, 'rb') as f:
                    exif_data = exif.Image(f)
                    if exif_data.has_exif:
                        # 获取日期字段
                        date_str = None
                        # 尝试不同的日期字段
                        for field in ['datetime_original', 'datetime']:
                            if hasattr(exif_data, field):
                                date_str = getattr(exif_data, field)
                                break
                        
                        if date_str:
                            # 尝试不同的日期格式
                            for fmt in ["%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                                try:
                                    return datetime.strptime(date_str, fmt)
                                except ValueError:
                                    continue
            except Exception as e:
                print(f"EXIF读取错误: {str(e)}")
                pass

        # 如果首选日期获取失败，使用备选日期
        stat = os.stat(file_path)
        fallback_source = self.settings["fallback_date_source"]
        
        if fallback_source == "修改日期":
            return datetime.fromtimestamp(stat.st_mtime)
        elif fallback_source == "创建日期":
            return datetime.fromtimestamp(stat.st_ctime)
        else:  # 当前日期
            return datetime.now()

class FileTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # ← PyQt5
        self.customContextMenuRequested.connect(self.show_context_menu)
        # 禁用双击编辑
        self.setEditTriggers(QTableWidget.NoEditTriggers)  # ← PyQt5

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        # 获取当前选中的行
        row = self.rowAt(pos.y())
        if row >= 0:
            # 添加删除选项
            delete_action = QAction("从列表中移除", self)
            delete_action.triggered.connect(lambda: self.remove_file(row))
            menu.addAction(delete_action)
            
            menu.addSeparator()
        
        # 添加清空列表选项
        clear_action = QAction("清空列表", self)
        clear_action.triggered.connect(self.clear_all)
        menu.addAction(clear_action)
        
        menu.exec_(self.mapToGlobal(pos))  # ← PyQt5: exec_

    def remove_file(self, row):
        if isinstance(self.parent, MainWindow):
            self.parent.files.pop(row)
            self.removeRow(row)
            # 更新状态栏显示
            self.parent.update_list_button_text()

    def clear_all(self):
        if isinstance(self.parent, MainWindow):
            self.parent.clear_files()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__app_name__} {__version__} —— {__author__}")
        
        # 设置应用程序图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            print(f"已加载图标: {icon_path}")
        else:
            print(f"警告: 图标文件不存在 - {icon_path}")
        
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
                outline: none;  /* 去掉表格的焦点边框 */
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f5f5f5;
            }
            QTableWidget::item:selected {
                background-color: #e8f0fe;
                color: #1a73e8;
                outline: none;  /* 去掉选中时的虚线边框 */
            }
            QTableWidget::item:focus {
                outline: none;  /* 去掉焦点时的虚线边框 */
                border: none;   /* 去掉边框 */
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
        self.settings = self.load_settings()
        self.has_renamed = False
        self.init_ui()
        self.setup_animations()

    def setup_animations(self):
        # 为开始按钮设置动画
        self.start_animation = QPropertyAnimation(self.action_btn, b"geometry")
        self.start_animation.setDuration(150)
        self.start_animation.setEasingCurve(QEasingCurve.OutCubic)  # ← PyQt5

        # 为设置按钮设置动画
        self.settings_animation = QPropertyAnimation(self.settings_btn, b"geometry")
        self.settings_animation.setDuration(150)
        self.settings_animation.setEasingCurve(QEasingCurve.OutCubic)  # ← PyQt5

        # 为展开按钮设置动画
        self.toggle_animation = QPropertyAnimation(self.toggle_list_btn, b"geometry")
        self.toggle_animation.setDuration(150)
        self.toggle_animation.setEasingCurve(QEasingCurve.OutCubic)  # ← PyQt5

    def enterEvent(self, event):
        # 鼠标进入按钮区域时触发动画
        if self.action_btn.underMouse():
            self.animate_button(self.action_btn, self.start_animation, True)
        elif self.settings_btn.underMouse():
            self.animate_button(self.settings_btn, self.settings_animation, True)
        elif self.toggle_list_btn.underMouse():
            self.animate_button(self.toggle_list_btn, self.toggle_animation, True)

    def leaveEvent(self, event):
        # 鼠标离开按钮区域时触发动画
        if self.action_btn.underMouse():
            self.animate_button(self.action_btn, self.start_animation, False)
        elif self.settings_btn.underMouse():
            self.animate_button(self.settings_btn, self.settings_animation, False)
        elif self.toggle_list_btn.underMouse():
            self.animate_button(self.toggle_list_btn, self.toggle_animation, False)

    def animate_button(self, button, animation, is_enter):
        # 获取按钮当前位置
        current_geometry = button.geometry()
        
        # 设置动画起始和结束位置
        if is_enter:
            # 鼠标进入时，按钮稍微上移
            animation.setStartValue(current_geometry)
            animation.setEndValue(current_geometry.adjusted(0, -2, 0, -2))
        else:
            # 鼠标离开时，按钮回到原位
            animation.setStartValue(current_geometry)
            animation.setEndValue(current_geometry.adjusted(0, 2, 0, 2))
        
        # 启动动画
        animation.start()

    def init_ui(self):
        self.setMinimumSize(500, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_layout = QStackedLayout(central_widget)

        # 主内容区
        self.main_panel = QWidget()
        layout = QVBoxLayout(self.main_panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 拖放区域
        self.drop_area = DropArea(self)
        self.drop_area.setMinimumHeight(200)
        layout.addWidget(self.drop_area)

        # 文件列表容器
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        # 文件列表
        self.file_list = FileTableWidget(self)
        self.file_list.setColumnCount(2)
        self.file_list.setHorizontalHeaderLabels(["文件名", "状态"])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # ← PyQt5
        self.file_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)    # ← PyQt5
        self.file_list.setColumnWidth(1, 60)
        self.file_list.setMinimumHeight(200)
        self.file_list.setVisible(False)
        self.file_list.setShowGrid(False)
        self.file_list.setSelectionBehavior(QTableWidget.SelectRows)  # ← PyQt5
        self.file_list.verticalHeader().setVisible(False)
        # 设置标题对齐方式
        self.file_list.horizontalHeaderItem(0).setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # ← PyQt5
        self.file_list.horizontalHeaderItem(1).setTextAlignment(Qt.AlignCenter)  # ← PyQt5
        # 添加平滑滚动
        self.file_list.setVerticalScrollMode(QTableWidget.ScrollPerPixel)  # ← PyQt5
        self.file_list.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)  # ← PyQt5
        list_layout.addWidget(self.file_list)
        
        list_container.hide()
        layout.addWidget(list_container)
        self.list_container = list_container

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 10, 0, 0)  # 添加上边距

        # 添加展开/隐藏按钮
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

        # 设置面板
        self.settings_panel = SettingsPanel(self)
        self.settings_panel.back_btn.clicked.connect(self.show_main_panel)
        self.stacked_layout.addWidget(self.settings_panel)
        self.stacked_layout.setCurrentWidget(self.main_panel)

        # 状态栏
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
            self.toggle_list_btn.setText("▲")  # 展开时显示向上三角形
            self.update_list_button_text()
            # 自动滚动到最后一行
            if self.file_list.rowCount() > 0:
                self.file_list.scrollToBottom()

    def hide_file_list(self):
        self.list_container.hide()
        self.file_list.setVisible(False)
        self.toggle_list_btn.setText("▼")  # 隐藏时显示向下三角形
        self.update_list_button_text()

    def show_message(self, message, duration=3000):
        """显示状态栏消息"""
        # 如果当前正在显示进度消息，不要覆盖它
        if duration == 0 and "正在重命名" in self.status_label.text():
            return
        self.status_label.setText(message)
        # 如果设置了持续时间，则定时恢复显示文件信息
        if duration > 0:
            QTimer.singleShot(duration, self.update_list_button_text)

    def update_list_button_text(self):
        if not self.files:
            self.status_label.setText("")  # 空列表时状态栏不显示任何内容
            return

        # 获取最新的文件信息
        latest_file = self.files[-1]
        file_name = os.path.basename(latest_file)
        if len(self.files) == 1:
            self.status_label.setText(file_name)
        else:
            self.status_label.setText(f"共{len(self.files)}个文件")
            # 确保状态栏文本不会太长
            if len(self.status_label.text()) > 50:
                self.status_label.setText(f"共{len(self.files)}个文件 - {file_name[:30]}...")

    def add_files(self, files):
        # 如果已经进行过重命名操作，则清空列表
        if self.has_renamed:
            self.clear_files()
            self.has_renamed = False

        # 添加新文件
        for file_path in files:
            if file_path not in self.files:  # 避免重复添加
                self.files.append(file_path)
                row = self.file_list.rowCount()
                self.file_list.insertRow(row)
                self.file_list.setItem(row, 0, QTableWidgetItem(os.path.basename(file_path)))
                self.file_list.setItem(row, 1, QTableWidgetItem("●"))
                self.file_list.item(row, 1).setTextAlignment(Qt.AlignCenter)  # ← PyQt5

        # 如果列表可见，则自动滚动到底部
        if self.file_list.isVisible():
            self.file_list.scrollToBottom()
        # 更新状态栏显示
        self.update_list_button_text()

    def show_settings(self):
        # 创建动画
        self.animation = QPropertyAnimation(self.stacked_layout.currentWidget(), b"geometry")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)  # ← PyQt5
        
        # 设置动画起始和结束位置
        start_geometry = self.stacked_layout.currentWidget().geometry()
        self.animation.setStartValue(start_geometry)
        
        # 切换到设置面板
        self.stacked_layout.setCurrentWidget(self.settings_panel)
        
        # 设置动画结束位置
        end_geometry = self.settings_panel.geometry()
        self.animation.setEndValue(end_geometry)
        
        # 启动动画
        self.animation.start()

    def show_main_panel(self):
        # 创建动画
        self.animation = QPropertyAnimation(self.stacked_layout.currentWidget(), b"geometry")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)  # ← PyQt5
        
        # 设置动画起始和结束位置
        start_geometry = self.stacked_layout.currentWidget().geometry()
        self.animation.setStartValue(start_geometry)
        
        # 切换到主面板
        self.stacked_layout.setCurrentWidget(self.main_panel)
        
        # 设置动画结束位置
        end_geometry = self.main_panel.geometry()
        self.animation.setEndValue(end_geometry)
        
        # 启动动画
        self.animation.start()

    def toggle_action(self):
        if self.action_btn.text() == "开始":
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

    def start_rename(self):
        if not self.files:
            return
        # 确保文件列表可见
        if not self.list_container.isVisible():
            self.show_file_list()
        self.worker = RenameWorker(self.files, self.settings)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.rename_finished)
        self.worker.start()
        # 添加状态栏提示
        self.show_message("正在重命名文件...", 0)  # 持续显示直到完成

    def stop_rename(self):
        if hasattr(self, 'worker'):
            self.worker.terminate()
            self.worker.wait()
        self.rename_finished(0)  # 传入0表示没有成功重命名的文件

    def update_progress(self, old_name, new_name):
        if "错误" not in new_name and "跳过" not in new_name and "已符合命名格式" not in new_name:
            # 更新文件列表中的路径
            for i in range(self.file_list.rowCount()):
                if self.file_list.item(i, 0).text() == os.path.basename(old_name):
                    self.file_list.item(i, 0).setText(os.path.basename(new_name))
                    self.file_list.item(i, 1).setText("✓")
                    self.file_list.item(i, 1).setForeground(QColor("#4CAF50"))
                    # 滚动到当前项
                    self.file_list.scrollToItem(self.file_list.item(i, 0))
                    break
            # 状态栏显示进度
            success_count = sum(1 for i in range(self.file_list.rowCount()) 
                              if self.file_list.item(i, 1).text() == "✓")
            total_count = self.file_list.rowCount()
            self.show_message(f"正在重命名... ({success_count}/{total_count})", 0)
            # 更新按钮文本显示进度
            self.action_btn.setText(f"停止 ({success_count}/{total_count})")
        else:
            # 如果是错误、跳过或已符合格式，更新列表状态
            for i in range(self.file_list.rowCount()):
                if self.file_list.item(i, 0).text() == os.path.basename(old_name):
                    if "错误" in new_name:
                        self.file_list.item(i, 1).setText("✗")
                        self.file_list.item(i, 1).setForeground(QColor("#F44336"))
                    elif "已符合命名格式" in new_name:
                        self.file_list.item(i, 1).setText("✓")
                        self.file_list.item(i, 1).setForeground(QColor("#4CAF50"))
                    else:
                        self.file_list.item(i, 1).setText("○")
                        self.file_list.item(i, 1).setForeground(QColor("#9E9E9E"))
                    # 滚动到当前项
                    self.file_list.scrollToItem(self.file_list.item(i, 0))
                    break

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
        # 只有在实际进行了重命名操作时才显示完成信息
        if success_count > 0:
            # 先清除进度消息
            self.status_label.setText("")
            # 然后显示完成消息
            QTimer.singleShot(100, lambda: self.show_message(f"✓ 已重命名 {success_count} 个文件", 3000))
            # 在拖动区域显示成功提示
            self.drop_area.show_success(success_count)
            self.has_renamed = True  # 标记已进行重命名操作
        else:
            self.show_message("没有文件被重命名", 3000)
            self.update_list_button_text()

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
        
        try:
            # 检查配置文件是否存在
            if not os.path.exists("settings.json"):
                # 如果不存在，创建默认配置文件
                with open("settings.json", "w", encoding="utf-8") as f:
                    json.dump(default_settings, f, ensure_ascii=False, indent=4)
                return default_settings
            
            # 读取现有配置
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # 检查必要的键是否存在，如果不存在则使用默认值
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            
            return settings
        except Exception as e:
            print(f"加载设置错误: {str(e)}")
            # 发生任何错误，返回默认设置
            return default_settings

    def clear_files(self):
        self.files.clear()
        self.file_list.setRowCount(0)
        self.drop_area.label.setText("拖放文件或文件夹到这里\n或点击选择文件")
        self.status_label.setText("")
        self.list_container.hide()
        self.has_renamed = False

if __name__ == '__main__':
    # 删除手动DPI设置，让Qt自行处理DPI
    app = QApplication(sys.argv)
    
    # 设置应用程序图标（在任务栏和任务管理器中显示）
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"已加载图标: {icon_path}")
    else:
        print(f"警告: 图标文件不存在 - {icon_path}")
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    # 设置默认字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())