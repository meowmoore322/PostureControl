import time
import winsound
import tkinter as tk
from config import BAD_POSTURE_DELAY, NOTIFY_COOLDOWN


class PostureNotifier:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.bad_posture_start = None
        self.last_notify_time = 0

    def update(self, is_bad_posture, mode_name):
        now = time.time()

        if is_bad_posture:
            if self.bad_posture_start is None:
                self.bad_posture_start = now

            duration = now - self.bad_posture_start
            if duration >= BAD_POSTURE_DELAY and (now - self.last_notify_time) >= NOTIFY_COOLDOWN:
                print(f"[УВЕДОМЛЕНИЕ] Сутулость {int(duration)} сек в режиме '{mode_name}'")
                self._show_popup(mode_name)
                self.last_notify_time = now
                return True
        else:
            self.bad_posture_start = None

        return False

    def _show_popup(self, mode_name):
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            pass

        popup = tk.Toplevel(self.parent)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#b71c1c")

        # Позиция в правом нижнем углу (с запасом от панели задач)
        w, h = 360, 100
        x = self.parent.winfo_screenwidth() - w - 30
        y = self.parent.winfo_screenheight() - h - 80
        popup.geometry(f"{w}x{h}+{x}+{y}")

        inner = tk.Frame(popup, bg="#261616", padx=15, pady=12)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        tk.Label(
            inner, text="⚠️ Пора выпрямить спину!",
            font=("Segoe UI", 12, "bold"), fg="#ff8a80", bg="#261616"
        ).pack(anchor="w")

        tk.Label(
            inner, text=f"Обнаружена сутулость ({mode_name}).\nРасправьте плечи!",
            font=("Segoe UI", 10), fg="white", bg="#261616", justify="left"
        ).pack(anchor="w", pady=(4, 0))

        popup.lift()
        popup.update()
        popup.after(4000, popup.destroy)
