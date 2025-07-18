import os
import tkinter as tk
from tkinter import messagebox, filedialog
from yt_dlp import YoutubeDL
import subprocess
from datetime import datetime


# Папки
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'youtube_downloads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'videos_output')
SPLIT_INPUT_DIR = os.path.join(BASE_DIR, 'BY_SPLIT')

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SPLIT_INPUT_DIR, exist_ok=True)


def get_cookies_file():
    filepath = filedialog.askopenfilename(
        title="Выберите файл куков",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
    if filepath:
        return filepath
    return None


def get_multiple_files():
    filepaths = filedialog.askopenfilenames(
        title="Выберите видеофайлы для разделения",
        filetypes=(("Video files", "*.mp4;*.avi;*.mov;*.mkv"), ("All files", "*.*")))
    return filepaths if filepaths else None


def download_video(url, cookies_file=None, browser=None):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'),
        'quiet': True,
    }
    
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file
    elif browser:
        ydl_opts['cookiesfrombrowser'] = (browser,)
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        if "cookies" in str(e).lower():
            return None
        raise e

    # Получаем последний скачанный файл
    files = sorted(os.listdir(DOWNLOADS_DIR), 
                  key=lambda x: os.path.getmtime(os.path.join(DOWNLOADS_DIR, x)), 
                  reverse=True)
    return os.path.join(DOWNLOADS_DIR, files[0]) if files else None

def split_video_by_minutes(video_path, output_root, minutes=1):
    video_name = video_path.split("/")[-1]
    if not video_path or not os.path.exists(video_path):
        raise FileNotFoundError("Видео файл не найден")

    # Создаем папку с именем файла (без расширения)
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
        output_path = os.path.join(output_folder, f"{video_name}_{part_number}.mp4")

        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-ss', str(start_time),
            '-t', str(minutes * 60),
            '-c', 'copy', output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    return output_folder

def start_download_with_cookies():
    cookies_file = get_cookies_file()
    if not cookies_file:
        return

    url = url_entry.get()
    if not url:
        messagebox.showerror("Ошибка", "Вставь ссылку на видео")
        return

    log_text.set("Скачиваем видео с куками...")
    root.update()

    try:
        video_path = download_video(url, cookies_file=cookies_file)
        if video_path:
            log_text.set(f"Готово: {os.path.basename(video_path)}")
        else:
            messagebox.showerror("Ошибка", "Не удалось скачать с указанными куками")
    except Exception as e:
        messagebox.showerror("Ошибка загрузки", str(e))


def start_download_and_split_with_cookies():
    cookies_file = get_cookies_file()
    if not cookies_file:
        return

    url = url_entry.get()
    if not url:
        messagebox.showerror("Ошибка", "Вставь ссылку на видео")
        return

    log_text.set("Скачиваем видео с куками...")
    root.update()

    try:
        video_path = download_video(url, cookies_file=cookies_file)
        if not video_path:
            messagebox.showerror("Ошибка", "Не удалось скачать с указанными куками")
            return

        log_text.set("Разрезаем видео...")
        root.update()

        output_folder = split_video_by_minutes(video_path, OUTPUT_DIR)
        log_text.set(f"Готово. Куски в {output_folder}")
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


def start_download():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Ошибка", "Вставь ссылку на видео")
        return

    log_text.set("Скачиваем видео...")
    root.update()

    try:
        video_path = download_video(url)
        if video_path:
            log_text.set(f"Готово: {os.path.basename(video_path)}")
        else:
            start_download_with_cookies()
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
        if not video_path:
            start_download_and_split_with_cookies()
            return

        log_text.set("Разрезаем видео...")
        root.update()

        output_folder = split_video_by_minutes(video_path, OUTPUT_DIR)
        log_text.set(f"Готово. Куски в {output_folder}")
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


def start_split():
    try:
        filepaths = get_multiple_files()
        if not filepaths:
            return

        log_text.set(f"Найдено {len(filepaths)} видео. Начинаем обработку...")
        root.update()

        success_count = 0
        for video_path in filepaths:
            try:
                output_folder = split_video_by_minutes(video_path, OUTPUT_DIR)
                success_count += 1
                log_text.set(f"Обработано: {os.path.basename(video_path)}")
                root.update()
            except Exception as e:
                log_text.set(f"Ошибка при обработке {os.path.basename(video_path)}: {str(e)}")
                root.update()

        log_text.set(f"Готово! Успешно обработано {success_count} из {len(filepaths)} видео")
        
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


# Интерфейс
root = tk.Tk()
root.title("YouTube Cutter by Артём")

tk.Label(root, text="Ссылка на YouTube:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Button(root, text="Скачать видео", command=start_download).grid(row=1, column=0, pady=5)
tk.Button(root, text="Скачать и разделить", command=start_download_and_split).grid(row=1, column=1, pady=5)
tk.Button(root, text="Разделить выбранные видео", command=start_split).grid(row=2, column=0, columnspan=2, pady=5)
log_text = tk.StringVar()
tk.Label(root, textvariable=log_text, fg="blue").grid(row=3, column=0, columnspan=2, pady=10)

root.mainloop()