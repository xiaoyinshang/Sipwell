import random
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

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


class SipwellApp:
    def __init__(self) -> None:
        self.is_quitting = False
        self.tray_icon: pystray.Icon | None = None

        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("420x180")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.status_var = tk.StringVar(value="正在初始化...")
        self.meme_count_var = tk.StringVar(value="表情包数量: 0")

        title = tk.Label(self.root, text="💧 Sipwell 喝水提醒", font=("Segoe UI", 18, "bold"))
        title.pack(pady=(16, 8))

        status = tk.Label(self.root, textvariable=self.status_var, font=("Segoe UI", 11))
        status.pack(pady=(2, 2))

        meme_count = tk.Label(self.root, textvariable=self.meme_count_var, font=("Segoe UI", 10))
        meme_count.pack(pady=(2, 12))

        open_dir_btn = tk.Button(
            self.root,
            text="打开 memes 文件夹",
            command=self.open_meme_folder,
            width=20,
        )
        open_dir_btn.pack(pady=(4, 12))

        hide_btn = tk.Button(
            self.root,
            text="最小化到后台托盘",
            command=self.hide_to_tray,
            width=20,
        )
        hide_btn.pack(pady=(0, 10))

        self.meme_files = self.load_memes()
        if not self.meme_files:
            messagebox.showwarning(
                "没有表情包",
                "未找到图片。请把你的喝水表情包放到 memes 文件夹后重启应用。",
            )

        self.update_status_for_next_reminder()
        self.setup_system_tray()
        self.schedule_next_hourly_popup()

    def load_memes(self) -> list[Path]:
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

    @staticmethod
    def next_top_of_hour(from_time: datetime | None = None) -> datetime:
        now = from_time or datetime.now()
        return (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))

    def milliseconds_until_next_hour(self) -> int:
        now = datetime.now()
        nxt = self.next_top_of_hour(now)
        delta = nxt - now
        return max(1000, int(delta.total_seconds() * 1000))

    def update_status_for_next_reminder(self) -> None:
        nxt = self.next_top_of_hour()
        self.status_var.set(f"下一次提醒: {nxt.strftime('%Y-%m-%d %H:%M')}")

    def schedule_next_hourly_popup(self) -> None:
        delay = self.milliseconds_until_next_hour()
        self.root.after(delay, self.hourly_reminder)

    def hourly_reminder(self) -> None:
        if self.meme_files:
            self.show_meme_popup(random.choice(self.meme_files))
        else:
            messagebox.showinfo("喝水提醒", "到整点啦，记得喝水 💧")

        self.meme_files = self.load_memes()
        self.update_status_for_next_reminder()
        self.schedule_next_hourly_popup()

    def show_meme_popup(self, meme_path: Path) -> None:
        self.show_window()
        popup = tk.Toplevel(self.root)
        popup.title("该喝水啦 💧")
        popup.attributes("-topmost", True)
        popup.resizable(False, False)

        # 控制表情包显示尺寸，避免窗口过大
        max_w, max_h = 520, 520

        image = Image.open(meme_path)
        image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        # 防止图片被垃圾回收
        popup._photo = photo  # type: ignore[attr-defined]

        msg = tk.Label(popup, text=f"整点到！先喝水，再继续忙～\n{meme_path.name}", font=("Segoe UI", 11))
        msg.pack(padx=12, pady=(12, 8))

        label = tk.Label(popup, image=photo)
        label.pack(padx=12, pady=8)

        close_btn = tk.Button(popup, text="我这就去喝", width=16, command=popup.destroy)
        close_btn.pack(pady=(4, 14))

        popup.update_idletasks()
        self.center_window(popup)

    def center_window(self, win: tk.Toplevel) -> None:
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def create_tray_icon_image(self) -> Image.Image:
        size = 64
        image = Image.new("RGBA", (size, size), (58, 134, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.ellipse((14, 8, 50, 44), fill=(255, 255, 255, 255))
        draw.rectangle((22, 36, 42, 56), fill=(255, 255, 255, 255))
        return image

    def setup_system_tray(self) -> None:
        icon_image = self.create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("显示主窗口", self.on_tray_show),
            pystray.MenuItem("立即喝水提醒", self.on_tray_test_reminder),
            pystray.MenuItem("退出", self.on_tray_quit),
        )
        self.tray_icon = pystray.Icon("sipwell", icon_image, APP_TITLE, menu)
        self.tray_icon.run_detached()

    def on_tray_show(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self.show_window)

    def on_tray_test_reminder(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self.hourly_reminder)

    def on_tray_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self.root.after(0, self.quit_app)

    def hide_to_tray(self) -> None:
        self.root.withdraw()
        if self.tray_icon:
            self.tray_icon.notify("Sipwell 已在后台运行", "应用已最小化到系统托盘，整点会继续提醒你喝水。")

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_app(self) -> None:
        self.is_quitting = True
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    app = SipwellApp()
    app.run()
