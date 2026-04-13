# Sipwell

一个 Windows 环境下的喝水提醒小应用：
- 每个整点弹出提醒窗口。
- 随机展示你收集的喝水表情包（图片）。
- 关闭主窗口不会退出，会最小化到系统托盘后台运行。

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
点击窗口右上角关闭按钮时，应用会隐藏到系统托盘继续运行。你可以在托盘图标菜单中：
- 显示主窗口
- 手动触发一次提醒（测试）
- 退出应用

## 可选：打包成 exe（Windows）

如果你不想每次用命令行启动，可以用 `pyinstaller` 打包：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed sipwell.py
```

打包后可执行文件在 `dist/sipwell.exe`。

## Windows 开机自启

如果你已经打包成：
`E:\xproject\20260413_Sipwell_v1\dist\sipwell.exe`

推荐用 **任务计划程序（Task Scheduler）**，比“启动文件夹”更稳定。

### 方式 A：双击脚本（推荐）

仓库里提供了脚本：

- `startup/install_startup.bat`：创建登录时自启任务
- `startup/uninstall_startup.bat`：删除自启任务

> 默认路径就是 `E:\xproject\20260413_Sipwell_v1\dist\sipwell.exe`。如果你以后换路径，请先编辑 `install_startup.bat` 顶部的 `EXE_PATH`。

### 方式 B：手动命令行创建

以管理员身份打开 CMD，执行：

```bat
schtasks /create /tn "SipwellHourlyReminder" /tr "\"E:\xproject\20260413_Sipwell_v1\dist\sipwell.exe\"" /sc onlogon /rl limited /f
```

删除自启任务：

```bat
schtasks /delete /tn "SipwellHourlyReminder" /f
```
