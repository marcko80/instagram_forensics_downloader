import instaloader
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
    
    def __init__(self):
        self.config = Config()
        self.base_path = Path(os.path.dirname(os.path.abspath(__file__)))
        self.logger = None
        self._setup_thread_lock()
    
    def _setup_thread_lock(self):
        """Inizializza il lock per operazioni thread-safe."""
        self.file_lock = threading.Lock()
        self.hash_lock = threading.Lock()
    
    def setup_logging(self, profile_path: Path) -> None:
        """Configura il logging sia su file che su console."""
        log_file = profile_path / f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        logging.basicConfig(
            filename=str(log_file),
            level=logging.DEBUG,
            format=self.config.LOG_FORMAT
        )
        
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        logging.getLogger('').addHandler(console)
        
        self.logger = logging.getLogger('instagram_downloader')
    
    def log_and_print(self, message: str, level: int = logging.INFO) -> None:
        """Thread-safe logging e printing."""
        with self.file_lock:
            self.logger.log(level, message)
            tqdm.write(message)
    
    @staticmethod
    def validate_profile_url(url: str) -> str:
        """Valida e estrae l'username dall'URL del profilo."""
        if not url or not isinstance(url, str):
            raise ValueError("URL non valido")
            
        valid_prefixes = (
            'http://instagram.com/',
            'https://instagram.com/',
            'http://www.instagram.com/',
            'https://www.instagram.com/'
        )
        
        if not any(url.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError("URL Instagram non valido")
            
        return url.rstrip('/').split('/')[-1]
    
    @contextmanager
    def temporary_directory(self, path: Path):
        """Context manager per la gestione della directory temporanea."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            yield path
        finally:
            if path.exists():
                shutil.rmtree(str(path))
    
    def calculate_md5(self, file_path: Path) -> str:
        """Calcola l'hash MD5 di un file in modo efficiente."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(self.config.CHUNK_SIZE), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def write_hash(self, file_path: Path, hash_file: Path) -> bool:
        """Scrive l'hash MD5 nel file in modo thread-safe."""
        try:
            md5_hash = self.calculate_md5(file_path)
            relative_path = os.path.relpath(file_path, hash_file.parent)
            hash_entry = f"{md5_hash} *{relative_path}\n"
            
            with self.hash_lock:
                with open(hash_file, "a", encoding='utf-8') as f:
                    f.write(hash_entry)
            
            self.log_and_print(f"Hash calcolato e salvato per: {relative_path}")
            return True
        except Exception as e:
            self.log_and_print(f"Errore nel calcolo o salvataggio MD5 per {file_path}: {e}", logging.ERROR)
            return False
    
    def json_to_txt(self, json_file: Path, txt_file: Path) -> None:
        """Converte un file JSON in formato TXT."""
        try:
            with open(json_file, 'r', encoding='utf-8') as jf:
                data = json.load(jf)
            
            with open(txt_file, 'w', encoding='utf-8') as tf:
                for key, value in data.items():
                    tf.write(f"{key}: {value}\n")
            
            self.log_and_print(f"File {json_file} convertito in {txt_file}")
        except Exception as e:
            self.log_and_print(f"Errore nella conversione da {json_file} a {txt_file}: {e}", logging.ERROR)
    
    def get_downloaded_posts(self, posts_path: Path) -> Set[str]:
        """Recupera l'elenco dei post già scaricati."""
        return {
            f.stem.split('_')[0] 
            for f in posts_path.glob('*.jpg')
        }
    
    @retry(stop=stop_after_attempt(Config.RETRY_ATTEMPTS),
           wait=wait_exponential(multiplier=1, min=4, max=10))
    def download_post_with_retry(self, L: instaloader.Instaloader,
                               post: instaloader.Post,
                               temp_path: Path) -> None:
        """Scarica un singolo post con logica di retry."""
        try:
            L.dirname_pattern = str(temp_path)
            L.download_post(post, target="")
            sleep(self.config.RATE_LIMIT_DELAY)  # Rate limiting
        except Exception as e:
            self.log_and_print(f"Tentativo di retry per il post {post.shortcode}: {e}", logging.WARNING)
            raise
    
    def process_downloaded_files(self, temp_path: Path, posts_path: Path,
                               hash_file: Path) -> None:
        """Processa i file scaricati, muovendoli e calcolando gli hash."""
        for filename in os.listdir(temp_path):
            src_path = temp_path / filename
            dst_path = posts_path / filename
            
            try:
                shutil.move(str(src_path), str(dst_path))
                self.log_and_print(f"File spostato: da {src_path} a {dst_path}")
                
                if dst_path.is_file():
                    if not filename.endswith('.txt'):
                        self.write_hash(dst_path, hash_file)
                    elif filename.endswith('.json'):
                        txt_file_path = dst_path.with_suffix('.txt')
                        self.json_to_txt(dst_path, txt_file_path)
                        
            except Exception as e:
                self.log_and_print(f"Errore nello spostamento del file {filename}: {e}",
                                 logging.ERROR)
    
    def download_profile(self, profile_url: str) -> None:
        """Scarica un profilo Instagram completo."""
        try:
            username = self.validate_profile_url(profile_url)
            profile_path = self.base_path / username
            profile_path.mkdir(parents=True, exist_ok=True)
            
            self.setup_logging(profile_path)
            
            # Inizializza Instaloader con le impostazioni di configurazione
            L = instaloader.Instaloader(**self.config.DOWNLOAD_SETTINGS)
            
            posts_path = profile_path / "posts"
            posts_path.mkdir(exist_ok=True)
            
            hash_file = profile_path / "hash.txt"
            with open(hash_file, 'w', encoding='utf-8') as f:
                f.write("# MD5 hashes dei file scaricati\n")
            
            self.log_and_print(f"Download del profilo: {username}")
            profile = instaloader.Profile.from_username(L.context, username)
            
            # Recupera i post già scaricati per il resume capability
            downloaded_posts = self.get_downloaded_posts(posts_path)
            posts = list(profile.get_posts())
            
            with self.temporary_directory(self.base_path / f"temp_download_{username}") as temp_path:
                with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
                    futures = []
                    
                    for post in tqdm(posts, desc=f"Download dei post di {username}"):
                        if post.shortcode in downloaded_posts:
                            self.log_and_print(f"Skip del post già scaricato: {post.shortcode}")
                            continue
                            
                        futures.append(
                            executor.submit(
                                self.download_post_with_retry,
                                L,
                                post,
                                temp_path
                            )
                        )
                    
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            self.log_and_print(f"Errore nel download: {e}", logging.ERROR)
                        
                        self.process_downloaded_files(temp_path, posts_path, hash_file)
            
            self.log_and_print(f"Download completato per il profilo {username}")
            self.log_and_print(f"File salvati in: {posts_path}")
            self.log_and_print(f"Hash MD5 salvati in: {hash_file}")
            
        except instaloader.exceptions.ProfileNotExistsException:
            self.log_and_print(f"Il profilo {username} non esiste o non è accessibile.",
                             logging.ERROR)
        except Exception as e:
            self.log_and_print(f"Si è verificato un errore durante il download: {e}",
                             logging.ERROR)
            self.log_and_print("Traceback completo:", logging.ERROR)
            self.log_and_print(traceback.format_exc(), logging.ERROR)

def main():
    """Funzione principale del programma."""
    try:
        downloader = InstagramDownloader()
        profile_url = input("Inserisci l'URL del profilo Instagram pubblico: ")
        downloader.download_profile(profile_url)
    except KeyboardInterrupt:
        print("\nOperazione interrotta dall'utente.")
        sys.exit(1)
    except Exception as e:
        print(f"Errore fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


