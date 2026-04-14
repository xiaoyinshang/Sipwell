# Sipwell 喝水提醒

一个简洁优雅的喝水提醒应用，帮助你养成规律喝水的好习惯。

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## 功能特性

### 核心功能
- **智能提醒**：支持 30分钟/1小时/2小时/整点 多种提醒间隔
- **免打扰时段**：可设置夜间免打扰（默认 22:00-08:00）
- **表情包提醒**：随机展示你收集的喝水表情包，让提醒更有趣
- **后台运行**：关闭主窗口自动最小化到系统托盘，不打扰工作

### 喝水记录
- **今日统计**：主窗口实时显示今日喝水次数
- **连续天数**：记录你的喝水连续天数
- **周统计**：查看本周喝水趋势和每日分布
- **历史记录**：自动保存最近30天的喝水记录

### 个性化设置
- **声音提醒**：可选开启/关闭提醒音效
- **开机自启动**：支持 Windows 开机自动启动
- **设置持久化**：所有设置自动保存，重启后依然有效

### 快捷操作
- **托盘菜单**：右键托盘图标快速访问常用功能
- **快捷键**：`Ctrl+Shift+W` 快速记录一杯水
- **双击托盘**：快速显示主窗口

## 快速开始

### 1. 安装 Python
建议使用 Python 3.10 或更高版本。

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 准备表情包（可选）
在项目根目录创建 `memes` 文件夹，把图片放进去，支持格式：
- `.png` / `.jpg` / `.jpeg`
- `.bmp` / `.gif` / `.webp`

> **注意**：本项目不提供表情包，请自行收集你喜欢的喝水提醒图片。没有表情包也能正常使用，会显示默认文字提醒。

### 4. 启动应用
```bash
python sipwell.py
```

## 使用指南

### 主窗口
- **下一次提醒**：显示下次提醒的具体时间
- **免打扰时段**：显示当前免打扰设置
- **今日喝水**：实时显示今天的喝水次数
- **连续天数**：显示连续喝水的天数记录
- **📊 统计按钮**：打开详细的喝水统计窗口
- **⚙ 设置按钮**：打开设置窗口

### 设置选项
在设置窗口中，你可以配置：

| 设置项 | 说明 |
|--------|------|
| 启用声音提醒 | 开启/关闭提醒弹窗时的音效 |
| 开机自动启动 | Windows 系统开机自动运行 |
| 提醒间隔 | 选择 30分钟/1小时/2小时 |
| 免打扰时段 | 设置免打扰的起止时间 |

点击**保存设置**后，所有更改会立即生效并持久化保存。

### 系统托盘
右键点击托盘图标可以：
- **显示主窗口**：恢复主窗口
- **打开 memes 文件夹**：快速管理表情包
- **设置**：打开设置窗口
- **立即喝水提醒**：手动触发一次提醒
- **退出**：完全退出应用

### 快捷键
- `Ctrl + Shift + W`：快速记录一杯水（无需弹窗确认）

## 数据存储

应用数据存储在以下位置：

**Windows:**
- 配置文件：`%APPDATA%\Sipwell\config.json`
- 喝水记录：`%APPDATA%\Sipwell\drink_records.json`

**macOS/Linux:**
- 配置文件：`~/.config/sipwell/config.json`
- 喝水记录：`~/.config/sipwell/drink_records.json`

## 打包成 exe（Windows）

如果不想用命令行启动，可以用 `pyinstaller` 打包：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed sipwell.py
```

打包后的可执行文件在 `dist/sipwell.exe`。

## 项目结构

```
Sipwell/
├── sipwell.py          # 主程序
├── requirements.txt    # 依赖列表
├── memes/             # 表情包文件夹（自建，默认空）
├── README.md          # 说明文档
├── DESIGN.md          # 设计文档
├── LICENSE            # MIT 许可证
└── .gitignore         # Git 忽略规则
```

## 上传到 GitHub

### 初始化仓库

```bash
# 在项目根目录执行
git init
```

### 添加文件

```bash
git add .gitignore
git add LICENSE
git add README.md
git add DESIGN.md
git add README_FONT.md
git add requirements.txt
git add sipwell.py
git add memes/.gitkeep
```

### 提交代码

```bash
git commit -m "Initial commit: Sipwell 喝水提醒应用 v1.0"
```

### 推送到 GitHub

```bash
# 在 GitHub 创建仓库后执行
git remote add origin https://github.com/yourusername/Sipwell.git
git branch -M main
git push -u origin main
```

### 关于表情包

本项目默认不包含表情包图片。如果你想在仓库中提供示例：

1. 将表情包放入 `memes/` 目录
2. 确保你有使用授权（建议使用原创或 CC0 授权图片）
3. 执行 `git add memes/图片名.jpg`
4. 重新提交推送

## 技术栈

- **GUI**: Tkinter + Pillow
- **系统托盘**: pystray
- **数据存储**: JSON

## 设计灵感

界面采用 Claude Design System 配色，以温暖的赤陶色（Terracotta）为主色调，搭配羊皮纸色（Parchment）背景，营造舒适自然的视觉体验。

## 许可证

MIT License
