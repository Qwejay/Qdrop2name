# Qdrop2name

Qdrop2name是一个用于批量重命名图片和视频文件的工具，它可以根据文件的EXIF信息、创建日期或修改日期重命名文件，使文件命名更加规范和有序。

## 功能特点

- 🖱️ 非常简单易用
- 📅 支持多种日期来源：
  - 拍摄日期（如果有EXIF信息）
  - 修改日期
  - 创建日期
  - 当前日期
  
- 🖼️ 支持多种文件格式：
  - 图片：JPG、JPEG、PNG、GIF、BMP、HEIC、HEIF、TIFF、TIF、WebP、RAW格式等
  - 视频：MP4、MOV、AVI、MKV、WMV、FLV、WEBM、M4V、3GP、MPG、MPEG等
- 📝 自定义命名模板
- 🔄 智能重名处理
- 🎨 现代化界面设计
- ⚡ 快速批量处理

## 下载&安装

### Windows 用户

1. 访问 [Releases](https://github.com/QwejayHuang/Qdrop2name/releases) 页面
2. 下载最新版本的 `Qdrop2name.exe`
3. 双击运行即可使用

### 从源码构建

1. 克隆仓库：
```bash
git clone https://github.com/QwejayHuang/Qdrop2name.git
cd Qdrop2name
```

2. 安装依赖：
```bash
pip install PyQt6 pillow exif pillow-heif
```

3. 运行程序：
```bash
python Qdrop2name.py
```

## 使用说明

1. 启动程序后，将文件或文件夹拖放到程序窗口中
2. 点击"⚙"按钮进入设置面板
3. 在设置面板中：
   - 设置命名模板
   - 选择日期来源
   - 配置重名处理方式
4. 点击"开始"按钮开始重命名
5. 等待处理完成

### 命名模板说明

可用变量：
- `{YYYY}` - 年份（如：2025）
- `{MM}` - 月份（如：04）
- `{DD}` - 日期（如：15）
- `{HH}` - 小时（如：12）
- `{mm}` - 分钟（如：28）
- `{SS}` - 秒钟（如：09）

示例：
- `{YYYY}{MM}{DD}_{HH}{mm}{SS}` → 20250415_122809.jpg
- `IMG-{YYYY}{MM}{DD}_{HH}{mm}{SS}` → IMGS-20250415_122809.jpg
- `Photo_{YYYY}-{MM}-{DD}` → Photo_2025-04-15.jpg

### 构建说明

使用 Nuitka 构建可执行文件：

```bash
python -m nuitka --standalone --disable-console --enable-plugin=pyqt6 --include-module=PyQt6.QtWidgets --include-module=PyQt6.QtCore --include-module=PyQt6.QtGui --include-module=PIL --include-module=exif --include-module=pillow_heif --include-data-files=icon.ico=icon.ico --onefile --nofollow-import-to=tkinter --windows-icon-from-ico=icon.ico --remove-output --jobs=1 --lto=yes --include-data-files=settings.json=settings.json Qdrop2name.py
```

## 更新日志

## 1.0.1 (2025-06-07)

### 功能改进
- 添加程序图标，在标题栏和任务栏中显示
- 文件列表自动滚动显示当前正在处理的项目
- 开始重命名操作时自动展开文件列表

### 问题修复
- 修复DPI感知问题，避免高分辨率屏幕上显示模糊
- 改进EXIF日期解析，增加对多种日期格式和字段的支持


## 1.0.0 (2025-06-02)

- 基础功能：支持根据EXIF日期重命名图片和视频文件
- 支持拖放功能，可直接拖放文件或文件夹
- 自定义命名格式
- 可设置日期来源（拍摄日期、修改日期、创建日期、当前日期）
- 支持对非媒体文件进行重命名
- 重名文件处理机制
- 现代化UI界面 

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 作者

- QwejayHuang

## 贡献

欢迎提交 Issue 和 Pull Request！
