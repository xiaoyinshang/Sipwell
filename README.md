# Sipwell

一个 Windows 环境下的喝水提醒小应用：
- 每个整点弹出提醒窗口。
- 随机展示你收集的喝水表情包（图片）。

## 快速开始

### 1) 安装 Python
建议使用 Python 3.10+。

### 2) 安装依赖
```bash
pip install -r requirements.txt
```

### 3) 准备表情包
在项目根目录创建（或使用已有）`memes` 文件夹，把图片放进去，支持：
- `.png`
- `.jpg` / `.jpeg`
- `.bmp`
- `.gif`
- `.webp`

### 4) 启动应用
```bash
python sipwell.py
```

应用会显示下一次整点提醒时间；到点后会弹出置顶窗口提醒你喝水。

## 可选：打包成 exe（Windows）

如果你不想每次用命令行启动，可以用 `pyinstaller` 打包：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed sipwell.py
```

打包后可执行文件在 `dist/sipwell.exe`。
