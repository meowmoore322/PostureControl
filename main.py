import time
import cv2
import customtkinter as ctk
from PIL import Image

from config import MODES
from pose_analyzer import PoseAnalyzer
from notifier import PostureNotifier
from stats_manager import StatsManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def format_time(seconds):
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}ч {minutes}м {secs}с"
    if minutes > 0:
        return f"{minutes}м {secs}с"
    return f"{secs}с"


class PostureApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PostureControl — Контроль осанки")
        self.geometry("1100x800")
        self.minsize(750, 550)

        self.cap = None
        self.is_running = False
        self.last_stat_time = 0
        self.loop_id = None  # Хранит ID таймера обновления кадров

        self.analyzer = PoseAnalyzer()
        self.notifier = PostureNotifier(self)
        self.stats = StatsManager()

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=15, pady=10)
        self.tab_monitor = self.tabs.add("Мониторинг")
        self.tab_stats = self.tabs.add("Статистика")

        self.build_monitor_ui()
        self.build_stats_ui()
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def build_monitor_ui(self):
        top_panel = ctk.CTkFrame(self.tab_monitor, corner_radius=10)
        top_panel.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(top_panel, text="Режим:", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=15, pady=12)

        mode_list = list(MODES.keys())
        default_mode = "Программирование / ПК"
        self.mode_var = ctk.StringVar(value=default_mode)

        ctk.CTkOptionMenu(
            top_panel, variable=self.mode_var, values=mode_list,
            width=230, height=34, command=self.change_mode
        ).pack(side="left", padx=5)

        self.desc_label = ctk.CTkLabel(top_panel, text=MODES[default_mode]["description"], text_color="gray75")
        self.desc_label.pack(side="left", padx=15)

        self.video_box = ctk.CTkFrame(self.tab_monitor, fg_color="#141414", corner_radius=10)
        self.video_box.pack(fill="both", expand=True, padx=10, pady=5)

        self.video_label = ctk.CTkLabel(self.video_box, text="Поставьте камеру сбоку и нажмите «Старт»", font=ctk.CTkFont(size=17))
        self.video_label.pack(fill="both", expand=True)

        self.status_bar = ctk.CTkLabel(
            self.tab_monitor, text="Ожидание запуска", height=40,
            font=ctk.CTkFont(size=16, weight="bold"), fg_color="#2b2b2b", corner_radius=8
        )
        self.status_bar.pack(fill="x", padx=10, pady=8)

        btn_panel = ctk.CTkFrame(self.tab_monitor, fg_color="transparent")
        btn_panel.pack(pady=8)

        self.btn_start = ctk.CTkButton(btn_panel, text="▶ Старт", width=170, height=44, fg_color="#2e7d32", hover_color="#1b5e20", command=self.start_camera)
        self.btn_start.pack(side="left", padx=15)

        self.btn_stop = ctk.CTkButton(btn_panel, text="■ Стоп", width=170, height=44, fg_color="#c62828", hover_color="#8e0000", state="disabled", command=self.stop_camera)
        self.btn_stop.pack(side="left", padx=15)

    def build_stats_ui(self):
        header = ctk.CTkFrame(self.tab_stats, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(header, text="Статистика за сегодня", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Обновить", width=110, command=self.update_stats_ui).pack(side="right", padx=5)
        ctk.CTkButton(header, text="Сбросить", width=110, fg_color="#424242", command=self.reset_stats).pack(side="right", padx=5)

        score_box = ctk.CTkFrame(self.tab_stats, corner_radius=10)
        score_box.pack(fill="x", padx=15, pady=8)

        self.percent_label = ctk.CTkLabel(score_box, text="Ровная осанка: 0%", font=ctk.CTkFont(size=18, weight="bold"))
        self.percent_label.pack(anchor="w", padx=20, pady=(12, 5))

        self.progress_bar = ctk.CTkProgressBar(score_box, height=18)
        self.progress_bar.pack(fill="x", padx=20, pady=(5, 15))
        self.progress_bar.set(0)

        grid = ctk.CTkFrame(self.tab_stats, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=8)
        grid.columnconfigure((0, 1, 2, 3), weight=1)

        self.card_total = self.make_card(grid, 0, "Всего за столом", "0с")
        self.card_good = self.make_card(grid, 1, "Спина ровная", "0с", "#66bb6a")
        self.card_bad = self.make_card(grid, 2, "Сутулость", "0с", "#ef5350")
        self.card_notify = self.make_card(grid, 3, "Напоминаний", "0", "#ffa726")

        modes_box = ctk.CTkFrame(self.tab_stats, corner_radius=10)
        modes_box.pack(fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(modes_box, text="Время по режимам:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(12, 6))
        self.modes_label = ctk.CTkLabel(modes_box, text="Нет данных", font=ctk.CTkFont(size=14), justify="left")
        self.modes_label.pack(anchor="w", padx=20)

        self.update_stats_ui()

    def make_card(self, parent, col, title, text, color="white"):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(card, text=title, text_color="gray70", font=ctk.CTkFont(size=13)).pack(pady=(10, 2))
        val = ctk.CTkLabel(card, text=text, text_color=color, font=ctk.CTkFont(size=19, weight="bold"))
        val.pack(pady=(2, 10))
        return val

    def update_stats_ui(self):
        data = self.stats.get_today_summary()
        self.percent_label.configure(text=f"Индекс здоровой осанки: {data['good_percent']}%")
        self.progress_bar.set(data["good_percent"] / 100.0)

        self.card_total.configure(text=format_time(data["total_sec"]))
        self.card_good.configure(text=format_time(data["good_sec"]))
        self.card_bad.configure(text=format_time(data["bad_sec"]))
        self.card_notify.configure(text=str(data["notifications"]))

        lines = [f"• {mode}: {format_time(sec)}" for mode, sec in data["modes"].items()]
        self.modes_label.configure(text="\n".join(lines) if lines else "Нет данных за сегодня")

    def reset_stats(self):
        self.stats.reset_today()
        self.update_stats_ui()

    def change_mode(self, selected_mode):
        self.desc_label.configure(text=MODES[selected_mode]["description"])

    def start_camera(self):
        if not self.is_running:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.video_label.configure(text="Ошибка: камера не найдена")
                return
            self.is_running = True
            self.last_stat_time = time.time()
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.video_label.configure(text="")
            self.process_loop()

    def stop_camera(self):
        if self.is_running:
            self.is_running = False

            # 1. Отменяем следующий запланированный кадр
            if self.loop_id is not None:
                self.after_cancel(self.loop_id)
                self.loop_id = None

            # 2. Отключаем физическую камеру
            if self.cap:
                self.cap.release()
                self.cap = None

            self.stats.save()
            self.update_stats_ui()

            # 3. Полностью пересоздаём виджет видео, чтобы стереть зависшую картинку
            self.video_label.destroy()
            self.video_label = ctk.CTkLabel(
                self.video_box, text="Камера выключена", font=ctk.CTkFont(size=17)
            )
            self.video_label.pack(fill="both", expand=True)

            self.status_bar.configure(text="Остановлено", fg_color="#2b2b2b")
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")

    def process_loop(self):
        if self.is_running and self.cap:
            ok, frame = self.cap.read()
            if ok:
                frame = cv2.flip(frame, 1)
                mode = self.mode_var.get()

                frame, is_bad, status = self.analyzer.process_frame(
                    frame, MODES[mode]["max_torso_angle"], MODES[mode]["max_neck_angle"]
                )

                if self.notifier.update(is_bad, mode):
                    self.stats.record_notification()

                now = time.time()
                if now - self.last_stat_time >= 1.0:
                    if status in ("Осанка в норме", "СУТУЛОСТЬ!"):
                        self.stats.record_second(is_bad, mode)
                        if int(now) % 15 == 0:
                            self.stats.save()
                    self.last_stat_time = now

                color = "#b71c1c" if is_bad else ("#1b5e20" if status == "Осанка в норме" else "#424242")
                self.status_bar.configure(text=status, fg_color=color)

                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                w, h = self.video_box.winfo_width() - 10, self.video_box.winfo_height() - 10
                if w > 20 and h > 20:
                    img.thumbnail((w, h), Image.Resampling.LANCZOS)

                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.video_label.configure(image=ctk_img)
                self.video_label.image = ctk_img

            self.loop_id = self.after(15, self.process_loop)

    def close_app(self):
        self.stop_camera()
        self.destroy()


if __name__ == "__main__":
    PostureApp().mainloop()
