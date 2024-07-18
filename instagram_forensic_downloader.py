import instaloader
import os
import hashlib
import json
import sys
import traceback
import logging
import shutil
from datetime import datetime

def setup_logging(base_path):
    log_file = os.path.join(base_path, f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    logging.basicConfig(filename=log_file, level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

def log_and_print(message, level=logging.INFO):
    logging.log(level, message)
    print(message)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def create_directory(path):
    try:
        os.makedirs(path, exist_ok=True)
        log_and_print(f"Directory created or already exists: {path}")
        return True
    except Exception as e:
        log_and_print(f"Error creating directory {path}: {e}", logging.ERROR)
        return False

def write_hash(file_path, hash_file):
    try:
        md5_hash = calculate_md5(file_path)
        relative_path = os.path.relpath(file_path, os.path.dirname(hash_file))
        hash_entry = f"{md5_hash} *{relative_path}\n"
        
        with open(hash_file, "a", encoding='utf-8') as f:
            f.write(hash_entry)
        
        log_and_print(f"Hash calculated and saved for: {relative_path}")
        return True
    except Exception as e:
        log_and_print(f"Error calculating or saving MD5 for {file_path}: {e}", logging.ERROR)
        return False

def json_to_txt(json_file, txt_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as jf:
            data = json.load(jf)
        
        with open(txt_file, 'w', encoding='utf-8') as tf:
            for key, value in data.items():
                tf.write(f"{key}: {value}\n")
        
        log_and_print(f"File {json_file} converted to {txt_file}")
    except Exception as e:
        log_and_print(f"Error converting {json_file} to {txt_file}: {e}", logging.ERROR)

def download_profile(profile_url):
    base_path = os.path.dirname(os.path.abspath(__file__))
    username = profile_url.rstrip('/').split('/')[-1]
    profile_path = os.path.join(base_path, username)
    
    if not create_directory(profile_path):
        return
    
    setup_logging(profile_path)
    
    L = instaloader.Instaloader(
        download_pictures=True,
        download_videos=True,
        download_video_thumbnails=True,
        download_geotags=False,
        download_comments=False,
        save_metadata=True,
        compress_json=False,
        dirname_pattern="{profile}",
    )

    # Setting up a custom logger for Instaloader
    instaloader_logger = logging.getLogger('instaloader')
    instaloader_logger.setLevel(logging.DEBUG)
    instaloader_logger.addHandler(logging.StreamHandler())
    
    try:
        log_and_print(f"Attempting to download profile: {username}")
        log_and_print(f"Profile path: {profile_path}")
        
        posts_path = os.path.join(profile_path, "posts")
        log_and_print(f"Posts path: {posts_path}")
        if not create_directory(posts_path):
            return
        
        hash_file = os.path.join(profile_path, "hash.txt")
        log_and_print(f"MD5 hash file will be saved in: {hash_file}")
        
        with open(hash_file, 'w', encoding='utf-8') as f:
            f.write("# MD5 hashes of downloaded files\n")
        
        log_and_print(f"Retrieving profile information for: {username}")
        profile = instaloader.Profile.from_username(L.context, username)
        
        log_and_print(f"Starting to download posts for: {username}")
        post_count = 0
        hash_count = 0
        
        temp_download_path = os.path.join(base_path, f"temp_download_{username}")
        create_directory(temp_download_path)
        log_and_print(f"Temporary folder created: {temp_download_path}")
        
        for post in profile.get_posts():
            try:
                log_and_print(f"Downloading post {post.shortcode}...")
                L.dirname_pattern = temp_download_path
                L.download_post(post, target="")
                post_count += 1
                
                log_and_print(f"Files in temporary folder before moving: {os.listdir(temp_download_path)}")
                
                for filename in os.listdir(temp_download_path):
                    src_path = os.path.join(temp_download_path, filename)
                    dst_path = os.path.join(posts_path, filename)
                    try:
                        shutil.move(src_path, dst_path)
                        log_and_print(f"File moved: from {src_path} to {dst_path}")
                    except Exception as e:
                        log_and_print(f"Error moving file {filename}: {e}", logging.ERROR)
                    
                    if os.path.isfile(dst_path):
                        if not filename.endswith('.txt'):
                            if write_hash(dst_path, hash_file):
                                hash_count += 1
                        elif filename.endswith('.json'):
                            txt_file_path = dst_path.replace('.json', '.txt')
                            json_to_txt(dst_path, txt_file_path)
                
                log_and_print(f"Files in temporary folder after moving: {os.listdir(temp_download_path)}")
                
                for filename in os.listdir(temp_download_path):
                    os.remove(os.path.join(temp_download_path, filename))
                
                log_and_print(f"Post {post.shortcode} downloaded and moved successfully.")
            except Exception as e:
                log_and_print(f"Error downloading or moving post {post.shortcode}: {e}", logging.ERROR)
        
        shutil.rmtree(temp_download_path)
        log_and_print(f"Temporary folder removed: {temp_download_path}")
        
        if os.path.exists(hash_file) and os.path.getsize(hash_file) > 0:
            log_and_print(f"MD5 hash file created successfully: {hash_file}")
            log_and_print(f"Total MD5 hashes calculated and saved: {hash_count}")
        else:
            log_and_print(f"ERROR: The MD5 hash file is empty or does not exist: {hash_file}", logging.ERROR)
        
        log_and_print(f"Download completed for public profile {username}")
        log_and_print(f"Total posts downloaded: {post_count}")
        log_and_print(f"Files saved in: {posts_path}")
        log_and_print(f"MD5 hashes saved in: {hash_file}")
        
        files_in_posts = os.listdir(posts_path)
        log_and_print(f"Files present in posts folder: {files_in_posts}")
        
    except instaloader.exceptions.ProfileNotExistsException:
        log_and_print(f"The profile {username} does not exist or is not accessible.", logging.ERROR)
    except Exception as e:
        log_and_print(f"An error occurred during download: {e}", logging.ERROR)
        log_and_print("Full traceback:", logging.ERROR)
        log_and_print(traceback.format_exc(), logging.ERROR)

if __name__ == "__main__":
    profile_url = input("Enter the public Instagram profile URL: ")
    download_profile(profile_url)




