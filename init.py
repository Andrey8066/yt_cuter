import os
import tkinter as tk
from tkinter import messagebox, filedialog
from yt_dlp import YoutubeDL
import subprocess
from datetime import datetime

# Папки
BASE_DIR = os.path.dirname(os.path.abspath(file))
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'youtube_downloads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'videos_output')
SPLIT_INPUT_DIR = os.path.join(BASE_DIR, 'BY_SPLIT')

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SPLIT_INPUT_DIR, exist_ok=True)

# Глобальный путь к cookies
cookies_path = None

def choose_cookies_file():
    global cookies_path
    path = filedialog.askopenfilename(title="Выбери cookies.txt", filetypes=[("Cookies File", "*.txt")])
    if path:
        cookies_path = path
        cookies_label.config(text=f"Cookies: {os.path.basename(path)}")
        log_text.set("Файл cookies подключён.")
    else:
        log_text.set("Файл cookies не выбран.")

def download_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'),
        'quiet': True,
    }

    if cookies_path:
        ydl_opts['cookies'] = cookies_path

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    files = sorted(os.listdir(DOWNLOADS_DIR), key=lambda x: os.path.getmtime(os.path.join(DOWNLOADS_DIR, x)))
    return os.path.join(DOWNLOADS_DIR, files[-1])


def split_video_by_minutes(video_path, output_root, minutes=1):
    date_folder = datetime.now().strftime("%Y-%m-%d")
    output_folder = os.path.join(output_root, date_folder)
    os.makedirs(output_folder, exist_ok=True)

    duration_cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', video_path
    ]
    result = subprocess.run(duration_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration = float(result.stdout)

    total_parts = int(duration // (minutes * 60)) + 1

    for i in range(total_parts):
        start_time = i * minutes * 60
        part_number = str(i + 1).zfill(3)
        output_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(video_path))[0]}_part_{part_number}.mp4")

        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-ss', str(start_time),
            '-t', str(minutes * 60),
            '-c:v', 'libx264', '-c:a', 'aac', output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    os.remove(video_path)


def start_download():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Ошибка", "Вставь ссылку на видео")
        return

    log_text.set("Скачиваем видео...")
    root.update()

    try:
        video_path = download_video(url)
        log_text.set(f"Готово: {os.path.basename(video_path)}")
    except Exception as e:
        messagebox.showerror("Ошибка загрузки", str(e))


def start_download_and_split():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Ошибка", "Вставь ссылку на видео")
        return

    log_text.set("Скачиваем видео...")
    root.update()

    try:
        video_path = download_video(url)
        log_text.set("Разрезаем видео...")
        root.update()

        split_video_by_minutes(video_path, OUTPUT_DIR)
        log_text.set("Готово. Все куски в videos_output/<дата>. Исходник удалён.")
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


def split_all_in_folder():
    files = [f for f in os.listdir(SPLIT_INPUT_DIR) if f.lower().endswith('.mp4')]
    if not files:
        messagebox.showinfo("Пусто", "Нет видео в папке BY_SPLIT")
        return

    log_text.set("Нарезаем видео из BY_SPLIT...")
    root.update()

    for filename in files:
        try:
            full_path = os.path.join(SPLIT_INPUT_DIR, filename)
            split_video_by_minutes(full_path, OUTPUT_DIR)
        except Exception as e:
            messagebox.showerror("Ошибка", f"{filename}: {e}")
            log_text.set("Все видео из BY_SPLIT обработаны и удалены.")


# GUI
root = tk.Tk()
root.title("YouTube Cutter by Артём")

tk.Label(root, text="Ссылка на YouTube:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Button(root, text="Скачать видео", command=start_download).grid(row=1, column=0, pady=5)
tk.Button(root, text="Скачать и разделить", command=start_download_and_split).grid(row=1, column=1, pady=5)
tk.Button(root, text="Разделить из папки BY_SPLIT", command=split_all_in_folder).grid(row=2, column=0, columnspan=2, pady=5)
tk.Button(root, text="Выбрать cookies.txt", command=choose_cookies_file).grid(row=3, column=0, columnspan=2, pady=5)

cookies_label = tk.Label(root, text="Cookies: не выбраны", fg="gray")
cookies_label.grid(row=4, column=0, columnspan=2)

log_text = tk.StringVar()
tk.Label(root, textvariable=log_text, fg="blue").grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()