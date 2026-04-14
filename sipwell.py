import random
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, font as tkfont

try:
    from PIL import Image, ImageDraw, ImageTk
    import pystray
except ImportError as exc:
    raise SystemExit(
        "缺少依赖，请先执行: pip install -r requirements.txt"
    ) from exc


APP_TITLE = "Sipwell 喝水提醒"
MEME_DIR = Path("memes")
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

# 配置文件路径
if os.name == 'nt':  # Windows
    CONFIG_DIR = Path(os.environ.get('APPDATA', Path.home() / 'AppData/Roaming')) / 'Sipwell'
else:  # macOS/Linux
    CONFIG_DIR = Path.home() / '.config/sipwell'
CONFIG_FILE = CONFIG_DIR / 'config.json'
DATA_FILE = CONFIG_DIR / 'drink_records.json'


# Claude Design System Colors
COLORS = {
    # Light theme
    "parchment": "#f5f4ed",
    "ivory": "#faf9f5",
    "near_black": "#141413",
    "olive_gray": "#5e5d59",
    "stone_gray": "#87867f",
    "charcoal_warm": "#4d4c48",
    "terracotta": "#c96442",
    "coral": "#d97757",
    "warm_sand": "#e8e6dc",
    "border_cream": "#f0eee6",
    "warm_silver": "#b0aea5",
    "dark_surface": "#30302e",
    # Dark theme
    "dark_bg": "#1a1a19",
    "dark_card": "#252523",
    "dark_text": "#e8e6e1",
    "dark_muted": "#9a9893",
    "dark_border": "#3a3a38",
}


def get_font_family(root: tk.Tk, preferred: list[str], fallback: str = "Microsoft YaHei") -> str:
    """Check available fonts and return the first available preferred font."""
    available = set(tkfont.families(root))
    for font_name in preferred:
        if font_name in available:
            return font_name
    return fallback


class SipwellApp:
    def __init__(self) -> None:
        self.is_quitting = False
        self.tray_icon: pystray.Icon | None = None
        self._popup_open: bool = False  # 标记是否有弹窗正在显示

        # 免打扰设置（默认）
        self.dnd_enabled = True  # 默认启用免打扰
        self.dnd_start_hour = 22  # 晚上10点
        self.dnd_end_hour = 8     # 早上8点

        # 提醒间隔设置（默认60分钟）
        self.reminder_interval = 60  # 分钟

        # 声音提醒设置（默认开启）
        self.sound_enabled = True

        # 开机自启动设置（默认关闭）
        self.autostart_enabled = False

        # 主题设置（默认浅色，可选：light, dark, auto）
        self.theme = "light"

        # 加载保存的设置
        self.load_settings()

        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("360x380")  # 增加高度
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # Configure main window with parchment background
        self.root.configure(bg=COLORS["parchment"])

        # Detect available fonts
        self.title_font_family = get_font_family(
            self.root, ["LXGW WenKai", "霞鹜文楷", "Microsoft YaHei", "PingFang SC"], "Microsoft YaHei"
        )
        self.body_font_family = get_font_family(
            self.root, ["Microsoft YaHei", "PingFang SC", "Source Han Sans SC"], "Microsoft YaHei"
        )

        self.status_var = tk.StringVar(value="正在初始化...")
        self.meme_count_var = tk.StringVar(value="表情包数量: 0")
        self.next_reminder_var = tk.StringVar(value="下一次提醒：--")
        self.dnd_display_var = tk.StringVar(value="[免打扰时段：22:00-8:00]")

        # 喝水记录
        self.drink_records: list[datetime] = []
        self.today_count_var = tk.StringVar(value="今日喝水: 0 次")
        self.streak_var = tk.StringVar(value="连续 0 天")

        # 加载喝水记录
        self.load_drink_records()

        # Main container with padding
        main_frame = tk.Frame(self.root, bg=COLORS["parchment"])
        main_frame.pack(fill="both", expand=True, padx=32, pady=24)

        # Title with serif-style Chinese font
        title = tk.Label(
            main_frame,
            text="Sipwell",
            font=(self.title_font_family, 32, "normal"),
            fg=COLORS["near_black"],
            bg=COLORS["parchment"],
        )
        title.pack(pady=(0, 4))

        # Subtitle
        subtitle = tk.Label(
            main_frame,
            text="喝水提醒",
            font=(self.title_font_family, 16, "normal"),
            fg=COLORS["olive_gray"],
            bg=COLORS["parchment"],
        )
        subtitle.pack(pady=(0, 20))

        # Status card (ivory background with border)
        status_card = tk.Frame(
            main_frame,
            bg=COLORS["ivory"],
            highlightbackground=COLORS["border_cream"],
            highlightthickness=1,
        )
        status_card.pack(fill="x", pady=(0, 20))

        # Next reminder line
        next_reminder_label = tk.Label(
            status_card,
            textvariable=self.next_reminder_var,
            font=(self.body_font_family, 12, "normal"),
            fg=COLORS["near_black"],
            bg=COLORS["ivory"],
        )
        next_reminder_label.pack(pady=(12, 4))

        # DND period line
        dnd_label = tk.Label(
            status_card,
            textvariable=self.dnd_display_var,
            font=(self.body_font_family, 10, "normal"),
            fg=COLORS["stone_gray"],
            bg=COLORS["ivory"],
        )
        dnd_label.pack(pady=(4, 12))

        # Meme count display below status card
        meme_count_frame = tk.Frame(main_frame, bg=COLORS["parchment"])
        meme_count_frame.pack(fill="x", pady=(0, 16))

        # Today's drink count (不显示表情包数量)
        today_count = tk.Label(
            meme_count_frame,
            textvariable=self.today_count_var,
            font=(self.body_font_family, 14, "normal"),
            fg=COLORS["terracotta"],
            bg=COLORS["parchment"],
        )
        today_count.pack()

        # Streak display
        streak_label = tk.Label(
            meme_count_frame,
            textvariable=self.streak_var,
            font=(self.body_font_family, 10, "normal"),
            fg=COLORS["olive_gray"],
            bg=COLORS["parchment"],
        )
        streak_label.pack(pady=(4, 0))

        # Buttons frame
        btn_frame = tk.Frame(main_frame, bg=COLORS["parchment"])
        btn_frame.pack()

        # Stats button
        stats_btn = tk.Button(
            btn_frame,
            text="📊 统计",
            command=self.open_stats,
            font=(self.body_font_family, 10, "normal"),
            bg=COLORS["warm_sand"],
            fg=COLORS["charcoal_warm"],
            activebackground=COLORS["border_cream"],
            activeforeground=COLORS["near_black"],
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
        )
        stats_btn.pack(side="left", padx=(0, 8))

        # Settings button
        settings_btn = tk.Button(
            btn_frame,
            text="⚙ 设置",
            command=self.open_settings,
            font=(self.body_font_family, 10, "normal"),
            bg=COLORS["warm_sand"],
            fg=COLORS["charcoal_warm"],
            activebackground=COLORS["border_cream"],
            activeforeground=COLORS["near_black"],
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
        )
        settings_btn.pack(side="left")

        self.meme_files = self.load_memes()
        if not self.meme_files:
            messagebox.showwarning(
                "没有表情包",
                "未找到图片。请把你的喝水表情包放到 memes 文件夹后重启应用。",
            )

        self.update_status_for_next_reminder()
        self.setup_system_tray()
        self.schedule_next_reminder_popup()
        self.setup_hotkeys()

    def load_settings(self) -> None:
        """从配置文件加载设置。"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.dnd_enabled = config.get('dnd_enabled', True)
                self.dnd_start_hour = config.get('dnd_start_hour', 22)
                self.dnd_end_hour = config.get('dnd_end_hour', 8)
                self.reminder_interval = config.get('reminder_interval', 60)
                self.sound_enabled = config.get('sound_enabled', True)
                self.autostart_enabled = config.get('autostart_enabled', False)
                self.theme = config.get('theme', 'light')
        except Exception:
            # 如果加载失败，使用默认值
            pass

    def save_settings(self) -> None:
        """保存设置到配置文件。"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            config = {
                'dnd_enabled': self.dnd_enabled,
                'dnd_start_hour': self.dnd_start_hour,
                'dnd_end_hour': self.dnd_end_hour,
                'reminder_interval': self.reminder_interval,
                'sound_enabled': self.sound_enabled,
                'autostart_enabled': self.autostart_enabled,
                'theme': self.theme,
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            # 保存失败静默处理
            pass

    def load_drink_records(self) -> None:
        """从文件加载喝水记录，只保留最近30天的记录。"""
        try:
            if DATA_FILE.exists():
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                records = data.get('records', [])
                # 解析记录并过滤掉30天前的
                cutoff = datetime.now() - timedelta(days=30)
                self.drink_records = []
                for r in records:
                    try:
                        dt = datetime.fromisoformat(r)
                        if dt > cutoff:
                            self.drink_records.append(dt)
                    except ValueError:
                        continue
                self.update_today_count()
        except Exception:
            self.drink_records = []

    def save_drink_records(self) -> None:
        """保存喝水记录到文件。"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            # 只保存最近30天的记录
            cutoff = datetime.now() - timedelta(days=30)
            recent_records = [r for r in self.drink_records if r > cutoff]
            data = {
                'records': [r.isoformat() for r in recent_records]
            }
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record_drink(self) -> None:
        """记录一次喝水。"""
        now = datetime.now()
        self.drink_records.append(now)
        self.save_drink_records()
        self.update_today_count()

    def update_today_count(self) -> None:
        """更新今日喝水次数和连续天数显示。"""
        today = datetime.now().date()
        count = sum(1 for r in self.drink_records if r.date() == today)
        self.today_count_var.set(f"今日喝水: {count} 次")
        self.streak_var.set(f"连续 {self.calculate_streak()} 天")

    def calculate_streak(self) -> int:
        """计算连续喝水天数。"""
        if not self.drink_records:
            return 0
        # 获取有记录的日期集合
        record_dates = set(r.date() for r in self.drink_records)
        today = datetime.now().date()
        streak = 0
        # 从今天开始向前检查
        check_date = today
        while check_date in record_dates:
            streak += 1
            check_date -= timedelta(days=1)
        # 如果今天没有记录，检查昨天是否有
        if today not in record_dates:
            yesterday = today - timedelta(days=1)
            if yesterday in record_dates:
                streak = 0
                check_date = yesterday
                while check_date in record_dates:
                    streak += 1
                    check_date -= timedelta(days=1)
            else:
                streak = 0
        return streak

    def calculate_week_stats(self) -> dict:
        """计算本周统计。"""
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())  # 本周一
        week_records = [r for r in self.drink_records if week_start <= r.date() <= today]
        daily_counts = {}
        for i in range(7):
            day = week_start + timedelta(days=i)
            daily_counts[day] = sum(1 for r in week_records if r.date() == day)
        return {
            "total": len(week_records),
            "daily": daily_counts,
            "week_start": week_start,
        }

    def play_notification_sound(self) -> None:
        """播放通知声音。"""
        if not self.sound_enabled:
            return
        try:
            # Windows 使用 winsound
            if os.name == 'nt':
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                # macOS/Linux 使用系统声音
                import subprocess
                subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'],
                             capture_output=True, check=False)
        except Exception:
            pass

    def set_autostart(self, enabled: bool) -> None:
        """设置开机自启动（Windows）。"""
        self.autostart_enabled = enabled
        try:
            if os.name == 'nt':
                import winreg
                run_key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE | winreg.KEY_READ
                )
                app_path = str(Path(__file__).resolve())
                if enabled:
                    winreg.SetValueEx(run_key, "Sipwell", 0, winreg.REG_SZ, f'pythonw "{app_path}"')
                else:
                    try:
                        winreg.DeleteValue(run_key, "Sipwell")
                    except FileNotFoundError:
                        pass
                run_key.Close()
        except Exception:
            pass

    def load_memes(self) -> list[Path]:
        MEME_DIR.mkdir(exist_ok=True)
        files = [
            path
            for path in MEME_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        return files

    def open_meme_folder(self) -> None:
        MEME_DIR.mkdir(exist_ok=True)
        import os
        os.startfile(MEME_DIR.resolve())

    def get_theme_color(self, key: str) -> str:
        """根据当前主题返回对应的颜色。"""
        theme_map = {
            "light": {
                "bg": COLORS["parchment"],
                "card": COLORS["ivory"],
                "text": COLORS["near_black"],
                "muted": COLORS["olive_gray"],
                "border": COLORS["border_cream"],
            },
            "dark": {
                "bg": COLORS["dark_bg"],
                "card": COLORS["dark_card"],
                "text": COLORS["dark_text"],
                "muted": COLORS["dark_muted"],
                "border": COLORS["dark_border"],
            },
        }
        return theme_map.get(self.theme, theme_map["light"]).get(key, COLORS["parchment"])

    def apply_theme(self) -> None:
        """应用当前主题到主窗口。"""
        bg_color = self.get_theme_color("bg")
        self.root.configure(bg=bg_color)
        MEME_DIR.mkdir(exist_ok=True)
        files = [
            path
            for path in MEME_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        self.meme_count_var.set(f"表情包数量: {len(files)}")
        return files

    def open_meme_folder(self) -> None:
        MEME_DIR.mkdir(exist_ok=True)
        import os

        os.startfile(MEME_DIR.resolve())

    def next_reminder_time(self, from_time: datetime | None = None) -> datetime:
        """计算下一次提醒时间，根据设置的间隔。"""
        now = from_time or datetime.now()
        if self.reminder_interval == 60:
            # 整点模式：下一个整点
            return (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        else:
            # 固定间隔模式：从当前时间向上取整到间隔倍数
            minutes_since_midnight = now.hour * 60 + now.minute
            next_interval = ((minutes_since_midnight // self.reminder_interval) + 1) * self.reminder_interval
            next_hour = next_interval // 60
            next_minute = next_interval % 60
            next_time = now.replace(hour=next_hour % 24, minute=next_minute, second=0, microsecond=0)
            if next_hour >= 24:
                next_time += timedelta(days=1)
            return next_time

    def milliseconds_until_next_reminder(self) -> int:
        now = datetime.now()
        nxt = self.next_reminder_time(now)
        delta = nxt - now
        return max(1000, int(delta.total_seconds() * 1000))

    def update_status_for_next_reminder(self) -> None:
        nxt = self.next_reminder_time()
        self.next_reminder_var.set(f"下一次提醒：{nxt.strftime('%Y-%m-%d %H:%M')}")

        # 更新免打扰时段显示
        if self.dnd_enabled:
            self.dnd_display_var.set(f"[免打扰时段：{self.dnd_start_hour:02d}:00-{self.dnd_end_hour:02d}:00]")
        else:
            self.dnd_display_var.set("[免打扰时段：已关闭]")

    def is_in_dnd_period(self) -> bool:
        """Check if current time is in do-not-disturb period."""
        if not self.dnd_enabled:
            return False
        now = datetime.now()
        current_hour = now.hour

        # Handle overnight DND period (e.g., 22:00 to 08:00)
        if self.dnd_start_hour > self.dnd_end_hour:
            # DND period spans midnight
            return current_hour >= self.dnd_start_hour or current_hour < self.dnd_end_hour
        else:
            # DND period within same day
            return self.dnd_start_hour <= current_hour < self.dnd_end_hour

    def schedule_next_reminder_popup(self) -> None:
        delay = self.milliseconds_until_next_reminder()
        self.root.after(delay, self.reminder_callback)

    def reminder_callback(self) -> None:
        # 防止重复弹窗：如果已经有弹窗在显示，跳过这次提醒
        if self._popup_open:
            self.update_status_for_next_reminder()
            self.schedule_next_reminder_popup()
            return

        # 检查是否在免打扰时段
        if self.is_in_dnd_period():
            self.update_status_for_next_reminder()
            self.schedule_next_reminder_popup()
            return

        if self.meme_files:
            self.show_meme_popup(random.choice(self.meme_files))
        else:
            messagebox.showinfo("喝水提醒", "到时间啦，记得喝水 💧")

        self.meme_files = self.load_memes()
        self.update_status_for_next_reminder()
        self.schedule_next_reminder_popup()

    def show_meme_popup(self, meme_path: Path) -> None:
        self._popup_open = True  # 标记弹窗已打开
        # 播放提醒声音
        self.play_notification_sound()
        popup = tk.Toplevel(self.root)
        popup.title("该喝水啦")
        popup.attributes("-topmost", True)
        popup.resizable(False, False)
        popup.configure(bg=COLORS["parchment"])

        # 控制表情包显示尺寸，避免窗口过大
        max_w, max_h = 520, 520

        image = Image.open(meme_path)
        image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        # 防止图片被垃圾回收
        popup._photo = photo  # type: ignore[attr-defined]

        # Main container
        container = tk.Frame(popup, bg=COLORS["parchment"], padx=24, pady=24)
        container.pack(fill="both", expand=True)

        # Title with serif font (using Chinese serif-like font)
        title = tk.Label(
            container,
            text="整点到",
            font=(self.title_font_family, 24, "normal"),
            fg=COLORS["near_black"],
            bg=COLORS["parchment"],
        )
        title.pack(pady=(0, 4))

        # Subtitle
        subtitle = tk.Label(
            container,
            text="先喝水，再继续忙",
            font=(self.body_font_family, 13, "normal"),
            fg=COLORS["olive_gray"],
            bg=COLORS["parchment"],
        )
        subtitle.pack(pady=(0, 16))

        # Image card with ivory background
        img_card = tk.Frame(
            container,
            bg=COLORS["ivory"],
            highlightbackground=COLORS["border_cream"],
            highlightthickness=1,
        )
        img_card.pack(pady=(0, 20))

        label = tk.Label(img_card, image=photo, bg=COLORS["ivory"])
        label.pack(padx=16, pady=16)

        # Brand Terracotta CTA button
        close_btn = tk.Button(
            container,
            text="我这就去喝",
            font=(self.body_font_family, 12, "normal"),
            bg=COLORS["terracotta"],
            fg=COLORS["ivory"],
            activebackground=COLORS["coral"],
            activeforeground=COLORS["ivory"],
            relief="flat",
            padx=32,
            pady=12,
            cursor="hand2",
            command=lambda: self.on_close_popup(popup),
        )
        close_btn.pack(pady=(0, 8))

        popup.update_idletasks()
        self.center_window(popup)

    def on_close_popup(self, popup: tk.Toplevel) -> None:
        """Handle popup close with occasional 'did you really drink' confirmation."""
        popup.destroy()

        # 30% 概率显示"你真的喝了吗"确认弹窗
        if random.random() < 0.3:
            self.show_did_you_drink_popup()
        else:
            # 直接记录喝水
            self.record_drink()
            self._popup_open = False

    def show_did_you_drink_popup(self) -> None:
        """Show the 'Did you really drink?' confirmation popup."""
        confirm_popup = tk.Toplevel(self.root)
        confirm_popup.title("认真喝水！")
        confirm_popup.attributes("-topmost", True)
        confirm_popup.resizable(False, False)
        confirm_popup.configure(bg=COLORS["parchment"])

        container = tk.Frame(confirm_popup, bg=COLORS["parchment"], padx=32, pady=28)
        container.pack(fill="both", expand=True)

        # Warning title
        title = tk.Label(
            container,
            text="你真的喝了吗？！！",
            font=(self.title_font_family, 22, "normal"),
            fg=COLORS["terracotta"],
            bg=COLORS["parchment"],
        )
        title.pack(pady=(0, 12))

        # Message
        msg = tk.Label(
            container,
            text="诚实回答，身体是你自己的 😤",
            font=(self.body_font_family, 12, "normal"),
            fg=COLORS["olive_gray"],
            bg=COLORS["parchment"],
        )
        msg.pack(pady=(0, 20))

        # Button frame
        btn_frame = tk.Frame(container, bg=COLORS["parchment"])
        btn_frame.pack()

        # Yes button (Terracotta)
        yes_btn = tk.Button(
            btn_frame,
            text="真的喝了 💧",
            command=lambda: [
                confirm_popup.destroy(),
                self.record_drink(),
                setattr(self, '_popup_open', False)
            ],
            font=(self.body_font_family, 11, "normal"),
            bg=COLORS["terracotta"],
            fg=COLORS["ivory"],
            activebackground=COLORS["coral"],
            activeforeground=COLORS["ivory"],
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
        )
        yes_btn.pack(side="left", padx=(0, 12))

        # No button (Warm Sand)
        no_btn = tk.Button(
            btn_frame,
            text="还没喝...",
            command=lambda: [confirm_popup.destroy(), setattr(self, '_popup_open', False)],
            font=(self.body_font_family, 11, "normal"),
            bg=COLORS["warm_sand"],
            fg=COLORS["charcoal_warm"],
            activebackground=COLORS["border_cream"],
            activeforeground=COLORS["near_black"],
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
        )
        no_btn.pack(side="left")

        confirm_popup.update_idletasks()
        self.center_window(confirm_popup)

    def center_window(self, win: tk.Toplevel) -> None:
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def create_tray_icon_image(self) -> Image.Image:
        size = 64
        # Use Terracotta brand color as base (#c96442)
        terracotta_rgb = (201, 100, 66)
        ivory_rgb = (250, 249, 245)
        image = Image.new("RGBA", (size, size), (*terracotta_rgb, 255))
        draw = ImageDraw.Draw(image)
        # Draw a water drop shape in ivory
        draw.ellipse((16, 10, 48, 42), fill=(*ivory_rgb, 255))
        draw.rectangle((26, 38, 38, 54), fill=(*ivory_rgb, 255))
        return image

    def setup_system_tray(self) -> None:
        icon_image = self.create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("显示主窗口", self.on_tray_show),
            pystray.MenuItem("打开 memes 文件夹", self.on_tray_open_folder),
            pystray.MenuItem("设置", self.on_tray_settings),
            pystray.MenuItem("立即喝水提醒", self.on_tray_test_reminder),
            pystray.MenuItem("退出", self.on_tray_quit),
        )
        self.tray_icon = pystray.Icon("sipwell", icon_image, APP_TITLE, menu)
        self.tray_icon.run_detached()

    def on_tray_show(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self.show_window)

    def on_tray_open_folder(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self.open_meme_folder)

    def on_tray_settings(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self.open_settings)

    def on_tray_test_reminder(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self.reminder_callback)

    def on_tray_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self.quit_app)

    def hide_to_tray(self) -> None:
        self.root.withdraw()
        if self.tray_icon:
            self.tray_icon.notify("Sipwell 已在后台运行", "应用已最小化到系统托盘，会继续提醒你喝水。")

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_app(self) -> None:
        self.is_quitting = True
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()

    def setup_hotkeys(self) -> None:
        """设置全局快捷键 Ctrl+Shift+W 快速记录喝水。"""
        try:
            # 绑定快捷键到根窗口
            self.root.bind("<Control-Shift-w>", lambda e: self.quick_record_drink())
            self.root.bind("<Control-Shift-W>", lambda e: self.quick_record_drink())
        except Exception:
            pass

    def quick_record_drink(self) -> None:
        """快速记录一杯水（不弹窗）。"""
        self.record_drink()
        if self.tray_icon:
            self.tray_icon.notify("已记录喝水一次 💧", "继续加油！")

    def open_stats(self) -> None:
        """打开统计详情窗口。"""
        stats_win = tk.Toplevel(self.root)
        stats_win.title("喝水统计")
        stats_win.resizable(False, False)
        stats_win.configure(bg=COLORS["parchment"])
        stats_win.geometry("320x400")

        # Main container
        container = tk.Frame(stats_win, bg=COLORS["parchment"], padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # Title
        title = tk.Label(
            container,
            text="喝水统计",
            font=(self.title_font_family, 24, "normal"),
            fg=COLORS["near_black"],
            bg=COLORS["parchment"],
        )
        title.pack(pady=(0, 20))

        # 连续天数
        streak_card = tk.Frame(container, bg=COLORS["ivory"],
                               highlightbackground=COLORS["border_cream"], highlightthickness=1)
        streak_card.pack(fill="x", pady=(0, 12))

        streak_title = tk.Label(
            streak_card,
            text="连续喝水",
            font=(self.body_font_family, 11, "normal"),
            fg=COLORS["olive_gray"],
            bg=COLORS["ivory"],
        )
        streak_title.pack(pady=(12, 0))

        streak_num = tk.Label(
            streak_card,
            text=f"{self.calculate_streak()} 天",
            font=(self.title_font_family, 36, "normal"),
            fg=COLORS["terracotta"],
            bg=COLORS["ivory"],
        )
        streak_num.pack(pady=(4, 12))

        # 本周统计
        week_stats = self.calculate_week_stats()
        week_card = tk.Frame(container, bg=COLORS["ivory"],
                             highlightbackground=COLORS["border_cream"], highlightthickness=1)
        week_card.pack(fill="x", pady=(0, 12))

        week_title = tk.Label(
            week_card,
            text=f"本周喝水: {week_stats['total']} 次",
            font=(self.body_font_family, 12, "normal"),
            fg=COLORS["charcoal_warm"],
            bg=COLORS["ivory"],
        )
        week_title.pack(pady=(12, 8))

        # 每日统计
        days_frame = tk.Frame(week_card, bg=COLORS["ivory"])
        days_frame.pack(pady=(0, 12))

        day_names = ["一", "二", "三", "四", "五", "六", "日"]
        for i, (date, count) in enumerate(week_stats['daily'].items()):
            day_frame = tk.Frame(days_frame, bg=COLORS["ivory"])
            day_frame.pack(side="left", padx=4)

            color = COLORS["terracotta"] if count > 0 else COLORS["warm_silver"]
            day_label = tk.Label(
                day_frame,
                text=day_names[i],
                font=(self.body_font_family, 10, "normal"),
                fg=color,
                bg=COLORS["ivory"],
            )
            day_label.pack()

            count_label = tk.Label(
                day_frame,
                text=str(count),
                font=(self.body_font_family, 9, "normal"),
                fg=color,
                bg=COLORS["ivory"],
            )
            count_label.pack()

        # 关闭按钮
        close_btn = tk.Button(
            container,
            text="关闭",
            command=stats_win.destroy,
            font=(self.body_font_family, 11, "normal"),
            bg=COLORS["terracotta"],
            fg=COLORS["ivory"],
            activebackground=COLORS["coral"],
            activeforeground=COLORS["ivory"],
            relief="flat",
            padx=24,
            pady=8,
            cursor="hand2",
        )
        close_btn.pack(pady=(8, 0))

        stats_win.update_idletasks()
        self.center_window(stats_win)

    def open_settings(self) -> None:
        """Open the settings window for do-not-disturb configuration."""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("设置")
        settings_win.resizable(False, False)
        settings_win.configure(bg=COLORS["parchment"])
        settings_win.geometry("360x520")

        # Main container
        container = tk.Frame(settings_win, bg=COLORS["parchment"], padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # Title
        title = tk.Label(
            container,
            text="设置",
            font=(self.title_font_family, 24, "normal"),
            fg=COLORS["near_black"],
            bg=COLORS["parchment"],
        )
        title.pack(pady=(0, 16))

        # Sound Section
        sound_frame = tk.Frame(container, bg=COLORS["ivory"], highlightbackground=COLORS["border_cream"], highlightthickness=1)
        sound_frame.pack(fill="x", pady=(0, 16))

        sound_inner = tk.Frame(sound_frame, bg=COLORS["ivory"], padx=16, pady=12)
        sound_inner.pack(fill="x")

        sound_var = tk.BooleanVar(value=self.sound_enabled)
        sound_check = tk.Checkbutton(
            sound_inner,
            text="启用声音提醒",
            variable=sound_var,
            font=(self.body_font_family, 12, "normal"),
            fg=COLORS["charcoal_warm"],
            bg=COLORS["ivory"],
            activebackground=COLORS["ivory"],
            selectcolor=COLORS["parchment"],
        )
        sound_check.pack(anchor="w")

        # Windows only: Autostart
        autostart_var = tk.BooleanVar(value=self.autostart_enabled)
        if os.name == 'nt':
            autostart_check = tk.Checkbutton(
                sound_inner,
                text="开机自动启动",
                variable=autostart_var,
                font=(self.body_font_family, 12, "normal"),
                fg=COLORS["charcoal_warm"],
                bg=COLORS["ivory"],
                activebackground=COLORS["ivory"],
                selectcolor=COLORS["parchment"],
            )
            autostart_check.pack(anchor="w", pady=(8, 0))
        else:
            # 非 Windows 系统也创建变量，但不在 UI 显示
            pass

        # Reminder Interval Section
        interval_frame = tk.Frame(container, bg=COLORS["ivory"], highlightbackground=COLORS["border_cream"], highlightthickness=1)
        interval_frame.pack(fill="x", pady=(0, 16))

        interval_inner = tk.Frame(interval_frame, bg=COLORS["ivory"], padx=16, pady=12)
        interval_inner.pack(fill="x")

        interval_label = tk.Label(
            interval_inner,
            text="提醒间隔：",
            font=(self.body_font_family, 12, "normal"),
            fg=COLORS["charcoal_warm"],
            bg=COLORS["ivory"],
        )
        interval_label.pack(side="left")

        interval_var = tk.IntVar(value=self.reminder_interval)
        interval_options = [
            (30, "30分钟"),
            (60, "1小时"),
            (120, "2小时"),
        ]
        interval_menu = tk.OptionMenu(
            interval_inner,
            interval_var,
            *[opt[0] for opt in interval_options],
        )
        interval_menu.config(
            font=(self.body_font_family, 11, "normal"),
            bg=COLORS["ivory"],
            fg=COLORS["charcoal_warm"],
            activebackground=COLORS["border_cream"],
            activeforeground=COLORS["near_black"],
            highlightthickness=0,
        )
        # 自定义显示文本
        interval_menu["menu"].config(
            font=(self.body_font_family, 11, "normal"),
            bg=COLORS["ivory"],
            fg=COLORS["charcoal_warm"],
        )
        interval_menu.pack(side="left")

        # 显示当前选择的文本
        interval_display = tk.Label(
            interval_inner,
            textvariable=tk.StringVar(value="1小时"),
            font=(self.body_font_family, 11, "normal"),
            fg=COLORS["olive_gray"],
            bg=COLORS["ivory"],
        )
        interval_display.pack(side="left", padx=(8, 0))

        def update_interval_display(*args):
            val = interval_var.get()
            for mins, text in interval_options:
                if mins == val:
                    interval_display.config(text=text)
                    break
        interval_var.trace_add("write", update_interval_display)
        update_interval_display()

        # DND Section
        dnd_frame = tk.Frame(container, bg=COLORS["ivory"], highlightbackground=COLORS["border_cream"], highlightthickness=1)
        dnd_frame.pack(fill="x", pady=(0, 16))

        dnd_inner = tk.Frame(dnd_frame, bg=COLORS["ivory"], padx=16, pady=16)
        dnd_inner.pack(fill="x")

        # DND Enable checkbox
        dnd_var = tk.BooleanVar(value=self.dnd_enabled)
        dnd_check = tk.Checkbutton(
            dnd_inner,
            text="启用免打扰时段",
            variable=dnd_var,
            font=(self.body_font_family, 12, "normal"),
            fg=COLORS["charcoal_warm"],
            bg=COLORS["ivory"],
            activebackground=COLORS["ivory"],
            selectcolor=COLORS["parchment"],
        )
        dnd_check.pack(anchor="w", pady=(0, 12))

        # Time selection frame
        time_frame = tk.Frame(dnd_inner, bg=COLORS["ivory"])
        time_frame.pack(fill="x")

        # Start time
        start_label = tk.Label(
            time_frame,
            text="从",
            font=(self.body_font_family, 11, "normal"),
            fg=COLORS["olive_gray"],
            bg=COLORS["ivory"],
        )
        start_label.pack(side="left")

        start_var = tk.StringVar(value=str(self.dnd_start_hour))
        start_spin = tk.Spinbox(
            time_frame,
            from_=0,
            to=23,
            width=2,
            textvariable=start_var,
            font=(self.body_font_family, 11, "normal"),
        )
        start_spin.pack(side="left", padx=(4, 0))

        start_suffix = tk.Label(
            time_frame,
            text=":00 到 ",
            font=(self.body_font_family, 11, "normal"),
            fg=COLORS["olive_gray"],
            bg=COLORS["ivory"],
        )
        start_suffix.pack(side="left")

        end_var = tk.StringVar(value=str(self.dnd_end_hour))
        end_spin = tk.Spinbox(
            time_frame,
            from_=0,
            to=23,
            width=2,
            textvariable=end_var,
            font=(self.body_font_family, 11, "normal"),
        )
        end_spin.pack(side="left", padx=(0, 0))

        end_suffix = tk.Label(
            time_frame,
            text=":00",
            font=(self.body_font_family, 11, "normal"),
            fg=COLORS["olive_gray"],
            bg=COLORS["ivory"],
        )
        end_suffix.pack(side="left")

        # Description
        desc = tk.Label(
            container,
            text="免打扰时段内不会弹出喝水提醒",
            font=(self.body_font_family, 10, "normal"),
            fg=COLORS["stone_gray"],
            bg=COLORS["parchment"],
        )
        desc.pack(pady=(0, 16))

        # Save button
        def save_settings():
            try:
                self.dnd_enabled = dnd_var.get()
                self.sound_enabled = sound_var.get()
                if os.name == 'nt':
                    self.set_autostart(autostart_var.get())
                self.dnd_start_hour = int(start_var.get())
                self.dnd_end_hour = int(end_var.get())
                self.reminder_interval = interval_var.get()
                # 保存到配置文件
                self.save_settings()
                # 更新主窗口显示
                self.update_status_for_next_reminder()
            except Exception as e:
                print(f"Save error: {e}")
            finally:
                settings_win.destroy()

        save_btn = tk.Button(
            container,
            text="保存设置",
            command=save_settings,
            font=(self.body_font_family, 11, "normal"),
            bg=COLORS["terracotta"],
            fg=COLORS["ivory"],
            activebackground=COLORS["coral"],
            activeforeground=COLORS["ivory"],
            relief="flat",
            padx=24,
            pady=8,
            cursor="hand2",
        )
        save_btn.pack()

        # Center the window
        settings_win.update_idletasks()
        self.center_window(settings_win)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    app = SipwellApp()
    app.run()
