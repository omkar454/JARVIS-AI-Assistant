import customtkinter as ctk
import time
import threading
import psutil
import socket
import datetime
import subprocess
import pyttsx3  # ✅ Using pyttsx3 now
from queue import Queue

# ---------------- SPEECH SYSTEM SETUP ----------------
tts_queue = Queue()

engine = pyttsx3.init()
engine.setProperty('rate', 200)
engine.setProperty('volume', 1.0)

def speak(text):
    tts_queue.put(text)

def speak_worker():
    while True:
        text = tts_queue.get()
        if text is None:
            break
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print("TTS Error:", e)
        tts_queue.task_done()

# -----------------------------------------------------
# --- No change in imports or TTS setup ---

class JarvisLoadingWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jarvis is Getting Ready...")
        self.geometry("900x600")
        self.config(bg="#000000")
        ctk.set_appearance_mode("dark")
        self.resizable(True, True)

        self.main_frame = ctk.CTkFrame(self, fg_color="#000000")
        self.main_frame.pack(fill="both", expand=True)

        self.canvas = ctk.CTkCanvas(self.main_frame, bg="#000000", highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

        self.progress_value = 0
        self.animation_speed = 35  # Slower ring animation
        self.loading_complete = False
        self.loading_task_index = 0
        self.visible_rings = 0

        self.loading_tasks = [
            "Initializing core systems...",
            "Loading essential modules...",
            "Establishing network connection...",
            "Preparing user interface...",
            "Finalizing setup...",
            "Jarvis is ready at your service!"
        ]

        self.globe_radius = 200
        self.jarvis_scale_factor = 0.18
        self.progress_percent = 0

        self.jarvis_text = self.canvas.create_text(
            0, 0,
            text="JARVIS",
            font=("Consolas", 48, "bold"),
            fill="#00BFFF",
            tags=("jarvis_text",)
        )

        self.hardware_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Consolas", 16),
            text_color="#00FFFF",
            bg_color="#000000",
            anchor="sw",
            justify="left"
        )
        self.hardware_label.place(relx=0.01, rely=0.95, anchor="sw")

        self.logs_textbox = ctk.CTkTextbox(
            self.main_frame,
            width=360,
            height=120,
            font=("Consolas", 16),
            text_color="#00FFFF",
            bg_color="#000000",
            fg_color="#000000",
            wrap="word",
            scrollbar_button_color="#222222",
            scrollbar_button_hover_color="#00FFFF"
        )
        self.logs_textbox.place(relx=0.99, rely=0.99, anchor="se")
        self.logs_textbox.insert("end", "[BOOT] System is starting...\n")
        self.logs_textbox.configure(state="disabled")

        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text="Starting...",
            font=("Consolas", 16, "bold"),
            text_color="#00FFFF",
            bg_color="#000000"
        )
        self.info_label.place(relx=0.5, rely=0.88, anchor="center")

        self.progressbar = ctk.CTkProgressBar(
            self.main_frame,
            orientation="horizontal",
            width=400,
            height=20,
            corner_radius=10,
            progress_color="#00FF00",
            fg_color="#111111"
        )
        self.progressbar.set(0)
        self.progressbar.place(relx=0.5, rely=0.93, anchor="center")

        self.time_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Consolas", 14),
            text_color="#00FFFF",
            bg_color="#000000"
        )
        self.time_label.place(relx=0.01, rely=0.03, anchor="nw")

        self.date_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Consolas", 14),
            text_color="#00FFFF",
            bg_color="#000000"
        )
        self.date_label.place(relx=0.99, rely=0.03, anchor="ne")

        self.bind("<Configure>", self.update_ui)
        self.after(500, self.reveal_next_ring)
        self.after(100, self.animate_loading_circles)
        self.after(500, self.update_loading_status)
        self.after(100, self.add_glow_effect)
        self.update_hardware_info()
        self.update_clock()

    def reveal_next_ring(self):
        if self.visible_rings < 4:
            self.visible_rings += 1
            self.after(1000, self.reveal_next_ring)  # Slightly slower

    def animate_loading_circles(self):
        self.canvas.delete("loading_circle")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        cx, cy = w // 2, h // 2
        globe_radius = min(w, h) * 0.45
        self.globe_radius = globe_radius

        if not self.loading_complete:
            for c in range(self.visible_rings):
                radius = globe_radius * (0.35 + c * 0.15)
                width = int(globe_radius * 0.02) + 1
                for i in range(16):
                    start_angle = int(self.progress_value + i * (360 / 16))
                    extent = 30
                    brightness = 100 + int(155 * ((i + c * 4) % 16 / 16))
                    color = f"#{0:02x}{brightness:02x}{255:02x}"
                    dash = (5, 5) if c % 2 == 0 else None

                    self.canvas.create_arc(
                        cx - radius, cy - radius, cx + radius, cy + radius,
                        start=start_angle, extent=extent,
                        outline=color, width=width, style="arc",
                        tags="loading_circle", dash=dash
                    )

            self.progress_value += 35  # Slower ring rotation
            self.progress_percent = (self.progress_value % 360) / 360.0
            self.after(self.animation_speed, self.animate_loading_circles)
        else:
            self.trigger_final_boot_animation()

    def trigger_final_boot_animation(self):
        def fade_out(opacity):
            if opacity <= 0:
                self.destroy()
                subprocess.Popen(["python", "jarvis_frontend1.py"])
            else:
                self.attributes('-alpha', opacity)
                self.after(50, lambda: fade_out(opacity - 0.05))
        fade_out(1.0)

    def update_loading_status(self):
        if not self.loading_complete and self.loading_task_index < len(self.loading_tasks):
            task = self.loading_tasks[self.loading_task_index]
            self.info_label.configure(text=task)
            self.log_boot_message(f"[BOOT] {task}")
            speak(task)
            self.loading_task_index += 1
            self.after(3000, self.update_loading_status)  # More delay between tasks

    def simulate_loading(self):
        for i in range(101):
            time.sleep(0.14)  # Slower progress bar
            percent = i / 100.0
            self.progress_percent = percent
            self.progressbar.set(percent)
            self.update_idletasks()
        self.loading_complete = True

    def update_ui(self, event=None):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        cx, cy = w // 2, h // 2
        globe_radius = min(w, h) * 0.45
        self.globe_radius = globe_radius
        jarvis_font_size = int(globe_radius * self.jarvis_scale_factor)
        self.canvas.itemconfig(self.jarvis_text, font=("Consolas", jarvis_font_size, "bold"))
        self.canvas.coords(self.jarvis_text, cx, cy)

    def update_hardware_info(self):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except:
            ip = "N/A"
        self.hardware_label.configure(text=f"CPU: {cpu}%\nRAM: {memory}%\nIP: {ip}")
        self.after(1000, self.update_hardware_info)

    def log_boot_message(self, message):
        self.logs_textbox.configure(state="normal")
        self.logs_textbox.insert("end", f"{message}\n")
        self.logs_textbox.see("end")
        self.logs_textbox.configure(state="disabled")

    def add_glow_effect(self):
        self.canvas.delete("jarvis_glow")
        x, y = self.canvas.coords(self.jarvis_text)
        for i in range(1, 6):
            size = 8 + i * 4
            self.canvas.create_oval(
                x - size, y - size,
                x + size, y + size,
                outline="#00BFFF",
                fill='',
                tags="jarvis_glow"
            )
        self.canvas.tag_raise(self.jarvis_text)
        self.after(100, self.add_glow_effect)

    def update_clock(self):
        now = datetime.datetime.now()
        self.time_label.configure(text=now.strftime("Time: %H:%M:%S"))
        self.date_label.configure(text=now.strftime("Date: %d-%m-%Y"))
        self.after(1000, self.update_clock)

if __name__ == "__main__":
    threading.Thread(target=speak_worker, daemon=True).start()
    app = JarvisLoadingWindow()
    threading.Thread(target=app.simulate_loading, daemon=True).start()
    app.mainloop()
