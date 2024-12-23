import os
import hashlib
import json
import sys
import traceback
import logging
import shutil
from datetime import datetime
from typing import Set, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from time import sleep
from functools import wraps
from tqdm import tqdm
import threading
from tenacity import retry, stop_after_attempt, wait_exponential
import instaloader

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

import queue

class TkinterHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.text_widget.after(100, self.check_queue)

    def emit(self, record):
        self.queue.put(record)

    def check_queue(self):
        while True:
            try:
                record = self.queue.get_nowait()
                msg = self.format(record) + '\n'
                self.text_widget.insert(tk.END, msg)
                self.text_widget.see(tk.END)
                self.text_widget.update_idletasks()
            except queue.Empty:
                break
        self.text_widget.after(100, self.check_queue)

@dataclass
class Config:
    """Configurazione centralizzata per il downloader."""
    DOWNLOAD_SETTINGS: Dict[str, bool] = None
    CHUNK_SIZE: int = 8192
    LOG_FORMAT: str = '%(asctime)s - %(levelname)s - %(message)s'
    MAX_WORKERS: int = 3
    RETRY_ATTEMPTS: int = 3
    RATE_LIMIT_DELAY: float = 1.0
    
    def __post_init__(self):
        if self.DOWNLOAD_SETTINGS is None:
            self.DOWNLOAD_SETTINGS = {
                'download_pictures': True,
                'download_videos': True,
                'download_video_thumbnails': True,
                'download_geotags': False,
                'download_comments': False,
                'save_metadata': True,
                'compress_json': False
            }

class InstagramDownloader:
    """Classe principale per il download dei profili Instagram."""
    
    def __init__(self, text_widget=None):
        self.config = Config()
        self.base_path = Path(os.path.dirname(os.path.abspath(__file__)))
        self.logger = logging.getLogger(__name__)
        self.text_widget = text_widget
        self._setup_thread_lock()

    def _setup_thread_lock(self):
        """Imposta un lock per la gestione dei thread."""
        self.thread_lock = threading.Lock()

    def download_profile(self, url, progress_callback=None):
        """Scarica il profilo Instagram dato un URL."""
        try:
            self.logger.info(f"Inizio download del profilo: {url}")
            loader = instaloader.Instaloader()

            # Autenticazione opzionale (sostituisci con username e password se necessario)
            # loader.login("username", "password")

            profile_name = url.split('/')[-1] or url.split('/')[-2]
            profile = instaloader.Profile.from_username(loader.context, profile_name)

            posts = profile.get_posts()
            total_posts = profile.mediacount

            for i, post in enumerate(posts, 1):
                loader.download_post(post, target=profile_name)
                if progress_callback:
                    progress_callback(i, total_posts)

            self.logger.info("Download completato con successo.")
        except instaloader.exceptions.LoginRequiredException:
            self.logger.error("Errore: Login richiesto per accedere a questo profilo.")
            raise
        except Exception as e:
            self.logger.error(f"Errore durante il download: {str(e)}")
            raise

if TKINTER_AVAILABLE:
    class InstagramDownloaderGUI:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Instagram Forensic Downloader")
            self.root.geometry("800x600")
            
            # Imposta l'icona se disponibile
            try:
                if getattr(sys, 'frozen', False):
                    # Se è un eseguibile
                    icon_path = os.path.join(sys._MEIPASS, "icon.ico")
                else:
                    # Se è uno script
                    icon_path = "icon.ico"
                self.root.iconbitmap(icon_path)
            except:
                pass  # Ignora se l'icona non è disponibile
            
            self.create_widgets()
            
        def create_widgets(self):
            # Frame principale
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # URL Input
            url_frame = ttk.Frame(main_frame)
            url_frame.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
            
            url_label = ttk.Label(url_frame, text="URL Profilo Instagram:")
            url_label.grid(row=0, column=0, padx=5)
            
            self.url_entry = ttk.Entry(url_frame, width=60)
            self.url_entry.grid(row=0, column=1, padx=5)
            
            # Pulsante Download
            self.download_button = ttk.Button(url_frame, text="Download", command=self.start_download)
            self.download_button.grid(row=0, column=2, padx=5)
            
            # Barra di progresso
            self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate")
            self.progress.grid(row=1, column=0, pady=10)
            
            # Area Log
            log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
            log_frame.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            self.log_text = scrolledtext.ScrolledText(log_frame, height=30)
            self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Configurazione Grid
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(2, weight=1)
            url_frame.columnconfigure(1, weight=1)
            log_frame.columnconfigure(0, weight=1)
            log_frame.rowconfigure(0, weight=1)
            
            # Configura logging
            handler = TkinterHandler(self.log_text)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logging.getLogger('').addHandler(handler)
            logging.getLogger('').setLevel(logging.INFO)
        
        def start_download(self):
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("Errore", "Inserisci un URL valido")
                return
            
            self.download_button.state(['disabled'])
            self.log_text.delete(1.0, tk.END)
            self.progress['value'] = 0
            
            def update_progress(current, total):
                progress_value = (current / total) * 100
                self.progress['value'] = progress_value
                self.root.update_idletasks()
            
            def download_thread():
                try:
                    downloader = InstagramDownloader(self.log_text)
                    downloader.download_profile(url, progress_callback=update_progress)
                    messagebox.showinfo("Completato", "Download completato con successo!")
                except Exception as e:
                    messagebox.showerror("Errore", f"Si è verificato un errore: {str(e)}")
                finally:
                    self.download_button.state(['!disabled'])
            
            thread = threading.Thread(target=download_thread)
            thread.start()
        
        def run(self):
            self.root.mainloop()

def main():
    """Funzione principale del programma."""
    if not TKINTER_AVAILABLE:
        print("Errore: tkinter non disponibile in questa configurazione.")
        return  # Evita di terminare il programma bruscamente
    try:
        app = InstagramDownloaderGUI()
        app.run()
    except Exception as e:
        print(f"Errore Fatale: {e}")  # Mostra l'errore senza interrompere bruscamente

if __name__ == "__main__":
    main()



