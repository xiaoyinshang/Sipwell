# Sipwell 字体说明

为了获得最佳视觉体验，建议安装以下中文字体。

## 推荐字体

### 1. 霞鹜文楷 (LXGW WenKai) ⭐ 首选
一款开源、文艺、优雅的中文字体，与 Claude 设计系统的温暖书卷气风格完美契合。

- **风格**: 楷体风格，温暖优雅
- **用途**: 应用标题、弹窗标题
- **下载地址**: https://github.com/lxgw/LxgwWenKai/releases

**安装方法**:
1. 前往 [GitHub Releases](https://github.com/lxgw/LxgwWenKai/releases) 下载最新版
2. 解压后双击 `.ttf` 或 `.ttc` 文件安装
3. 重启 Sipwell 应用即可生效

### 2. 系统自带备选字体
如果未安装霞鹜文楷，应用会自动使用以下系统字体：

| 系统 | 备选字体 |
|------|----------|
| Windows | 微软雅黑 (Microsoft YaHei) |
| macOS | 苹方 (PingFang SC) |
| Linux | 思源黑体 (Source Han Sans) |

## 字体回退机制

应用使用以下字体优先级：

```
标题: LXGW WenKai → 霞鹜文楷 → Microsoft YaHei → PingFang SC
正文: Microsoft YaHei → PingFang SC → Source Han Sans SC
```

如果首选字体未安装，tkinter 会自动尝试下一个字体，确保界面始终可读。

## 快速安装脚本 (Windows)

```powershell
# 使用 PowerShell 下载并安装霞鹜文楷
$url = "https://github.com/lxgw/LxgwWenKai/releases/download/v1.510/LXGWWenKai-Regular.ttf"
$out = "$env:TEMP\LXGWWenKai-Regular.ttf"
Invoke-WebRequest -Uri $url -OutFile $out
Copy-Item $out "C:\Windows\Fonts\"
```
