import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import hashlib
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from queue import Queue
import time

class GameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("MTA Developers Launcher v1.1 | by e1ectr0venik")
        
        # Конфигурационные параметры
        self.game_executable = "MTA/Multi Theft Auto.exe"       # Путь к клиенту
        self.server_executable = "dev/MTA Server.exe"           # Путь к серверу
        self.ignore_list = ["logs"]                             # Игнорируемые элементы и папки
        
        self.root.resizable(False, False)
        self.root.geometry("700x500")

        # Центрирование окна
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Конфигурация сервера
        self.base_url = "http://ip/"                # Сюда указать IP или домен откуда будут браться все файлы.
        self.version_url = urljoin(self.base_url, "version.xml")
        self.local_version_path = "version.xml"
        
        # Настройки загрузки
        self.max_threads = 4
        self.download_queue = Queue()
        self.active_threads = 0
        self.download_speeds = []
        self.last_update_time = time.time()
        self.total_operations = 0
        self.completed_operations = 0
        
        # GUI элементы
        self.create_widgets()
        self.check_versions()
    
    def create_widgets(self):
        # Версии
        self.version_frame = ttk.LabelFrame(self.root, text="Versions")
        self.version_frame.pack(padx=10, pady=5, fill="x")
        
        self.local_version_label = ttk.Label(self.version_frame, text="Local Version: Checking...")
        self.local_version_label.pack(side="left", padx=5)
        
        self.server_version_label = ttk.Label(self.version_frame, text="Server Version: Checking...")
        self.server_version_label.pack(side="right", padx=5)
        
        # Настройки потоков
        self.settings_frame = ttk.LabelFrame(self.root, text="Settings")
        self.settings_frame.pack(padx=10, pady=5, fill="x")
        
        ttk.Label(self.settings_frame, text="Threads:").pack(side="left", padx=5)
        self.threads_spinbox = ttk.Spinbox(self.settings_frame, from_=1, to=16, width=5)
        self.threads_spinbox.pack(side="left", padx=5)
        self.threads_spinbox.set(4)
        
        # Кнопки
        self.btn_frame = ttk.Frame(self.root)
        self.btn_frame.pack(padx=10, pady=5, fill="x")
        
        self.launch_btn = ttk.Button(self.btn_frame, text="Launch Game", command=self.launch_game)
        self.launch_btn.pack(side="left", padx=2)
        
        self.server_btn = ttk.Button(self.btn_frame, text="Start Server", command=self.start_server)
        self.server_btn.pack(side="left", padx=2)
        
        self.update_btn = ttk.Button(self.btn_frame, text="Update Game", state="disabled", command=self.start_update)
        self.update_btn.pack(side="left", padx=2)
        
        self.repair_btn = ttk.Button(self.btn_frame, text="Repair Game", command=self.repair_game)
        self.repair_btn.pack(side="left", padx=2)
        
        # Прогресс
        self.progress_frame = ttk.LabelFrame(self.root, text="Progress")
        self.progress_frame.pack(padx=10, pady=5, fill="x")
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", padx=5, pady=2)
        
        self.status_label = ttk.Label(self.progress_frame, text="Status: Idle")
        self.status_label.pack()
        
        self.speed_label = ttk.Label(self.progress_frame, text="Speed: 0 KB/s")
        self.speed_label.pack()
        
        # Логи
        self.log_text = tk.Text(self.root, height=10, state="disabled")
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)
    
    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
    
    def check_versions(self):
        threading.Thread(target=self._check_versions_thread, daemon=True).start()
    
    def _check_versions_thread(self):
        try:
            local_version = self.get_local_version()
            server_version = self.get_server_version()
            
            self.root.after(0, lambda: self.local_version_label.config(
                text=f"Local Version: {local_version or 'Not installed'}"
            ))
            self.root.after(0, lambda: self.server_version_label.config(
                text=f"Server Version: {server_version or 'Unknown'}"
            ))
            
            if server_version and local_version != server_version:
                self.root.after(0, lambda: self.update_btn.config(state="normal"))
                self.log("Update available!")
            else:
                self.root.after(0, lambda: self.update_btn.config(state="disabled"))
                
        except Exception as e:
            self.log(f"Error checking versions: {str(e)}")
    
    def get_local_version(self):
        if os.path.exists(self.local_version_path):
            tree = ET.parse(self.local_version_path)
            return tree.findtext("version")
        return None
    
    def get_server_version(self):
        response = requests.get(self.version_url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        return root.findtext("version")
    
    def start_update(self):
        self.max_threads = int(self.threads_spinbox.get())
        self.update_btn.config(state="disabled")
        self.repair_btn.config(state="disabled")
        self.progress_bar["value"] = 0
        self.download_speeds = []
        threading.Thread(target=self.update_game, daemon=True).start()
    
    def update_game(self):
        try:
            self.log("Starting update...")
            self.root.after(0, lambda: self.status_label.config(text="Status: Checking files..."))
            
            manifest_url = urljoin(self.base_url, "files_manifest.xml")
            response = requests.get(manifest_url)
            response.raise_for_status()
            
            server_files = ET.fromstring(response.content)
            files_to_download = []
            total_files = 0
            self.total_operations = 0
            self.completed_operations = 0
            
            # Первый проход: подсчёт файлов для проверки
            for file_elem in server_files.findall("file"):
                file_path = file_elem.findtext("path")
                if self.should_ignore(file_path):
                    continue
                total_files += 1
            self.total_operations = total_files
            
            # Второй проход: проверка хешей
            for file_elem in server_files.findall("file"):
                file_path = file_elem.findtext("path")
                if self.should_ignore(file_path):
                    continue
                
                server_hash = file_elem.findtext("hash")
                local_path = os.path.join(".", file_path)
                
                self.log(f"Checking {file_path}...")
                self.root.after(0, lambda: self.status_label.config(text=f"Checking: {file_path}"))
                
                need_download = True
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        local_hash = hashlib.md5(f.read()).hexdigest()
                    if local_hash == server_hash:
                        need_download = False
                
                if need_download:
                    files_to_download.append({
                        "url": urljoin(self.base_url, file_path),
                        "path": local_path,
                        "size": int(file_elem.findtext("size", 0))
                    })
                
                self.completed_operations += 1
                self._update_progress(self.completed_operations, self.total_operations)
            
            if not files_to_download:
                self.log("All files are up to date!")
                self.root.after(0, lambda: self.status_label.config(text="Status: Up to date"))
                return
            
            self.log(f"Found {len(files_to_download)} files to update")
            self.total_operations = len(files_to_download)
            self.completed_operations = 0
            
            # Добавление файлов в очередь загрузки
            for file_info in files_to_download:
                self.download_queue.put(file_info)
            
            # Запуск потоков загрузки
            self.total_downloaded = 0
            self.total_size = sum(f["size"] for f in files_to_download)
            self.root.after(0, lambda: self.status_label.config(text="Status: Downloading..."))
            
            for _ in range(min(self.max_threads, len(files_to_download))):
                self.active_threads += 1
                threading.Thread(target=self.download_worker, daemon=True).start()
            
            threading.Thread(target=self.monitor_speed, daemon=True).start()
            
        except Exception as e:
            self.log(f"Update failed: {str(e)}")
            self.root.after(0, lambda: self.status_label.config(text="Status: Error"))
            self.root.after(0, lambda: self.update_btn.config(state="normal"))
            self.root.after(0, lambda: self.repair_btn.config(state="normal"))
    
    def should_ignore(self, file_path):
        for item in self.ignore_list:
            if item in file_path.split(os.sep):
                self.log(f"Ignoring {file_path}")
                return True
        return False
    
    def download_worker(self):
        while not self.download_queue.empty():
            try:
                file_info = self.download_queue.get_nowait()
                self.download_file(file_info["url"], file_info["path"], file_info["size"])
                self.completed_operations += 1
                self._update_progress(self.completed_operations, self.total_operations)
            except:
                break
        
        self.active_threads -= 1
        if self.active_threads == 0:
            self.finish_update()
    
    def finish_update(self):
        try:
            version_response = requests.get(self.version_url)
            version_response.raise_for_status()
            with open(self.local_version_path, "wb") as f:
                f.write(version_response.content)
            
            self.log("Update completed successfully!")
            self.root.after(0, lambda: self.status_label.config(text="Status: Completed"))
        except Exception as e:
            self.log(f"Error saving version file: {str(e)}")
            self.root.after(0, lambda: self.status_label.config(text="Status: Error"))
        finally:
            self.root.after(0, self.check_versions)
            self.root.after(0, lambda: self.update_btn.config(state="normal"))
            self.root.after(0, lambda: self.repair_btn.config(state="normal"))
    
    def monitor_speed(self):
        last_bytes = 0
        while self.active_threads > 0:
            time.sleep(1)
            current_bytes = self.total_downloaded
            delta_bytes = current_bytes - last_bytes
            last_bytes = current_bytes
            
            speed_kb = delta_bytes / 1024
            speed_mb = speed_kb / 1024
            
            if speed_mb >= 1:
                speed_text = f"Speed: {speed_mb:.2f} MB/s"
            else:
                speed_text = f"Speed: {speed_kb:.2f} KB/s"
            
            self.root.after(0, lambda: self.speed_label.config(text=speed_text))
    
    def _update_progress(self, processed, total):
        progress = (processed / total) * 100
        self.root.after(0, lambda: self.progress_bar.config(value=progress))
    
    def download_file(self, url, save_path, file_size):
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            start_time = time.time()
            
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                downloaded = 0
                chunk_size = 1024 * 8
                
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            self.total_downloaded += len(chunk)
            
            elapsed = time.time() - start_time
            speed = file_size / elapsed if elapsed > 0 else 0
            speed_kb = speed / 1024
            speed_mb = speed_kb / 1024
            
            speed_text = f"{speed_mb:.2f} MB/s" if speed_mb >= 1 else f"{speed_kb:.2f} KB/s"
            self.log(f"Downloaded {os.path.basename(save_path)} ({speed_text})")
            
        except Exception as e:
            self.log(f"Error downloading {url}: {str(e)}")
            raise
    
    def repair_game(self):
        self.log("Starting repair...")
        self.start_update()
    
    def launch_game(self):
        if os.path.exists(self.game_executable):
            os.startfile(self.game_executable)
        else:
            messagebox.showerror("Error", f"Game executable not found at: {self.game_executable}")
    
    def start_server(self):
        if os.path.exists(self.server_executable):
            os.startfile(self.server_executable)
        else:
            messagebox.showerror("Error", f"Server executable not found at: {self.server_executable}")

if __name__ == "__main__":
    root = tk.Tk()
    launcher = GameLauncher(root)
    root.mainloop()