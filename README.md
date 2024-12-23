# Instagram Forensic Downloader

## Overview
The **Instagram Forensic Downloader** is a Python-based GUI application designed to download Instagram profiles for forensic purposes. The tool supports downloading images, videos, and metadata while calculating SHA1 hashes for `.jpg` and `.mp4` files to ensure data integrity.

## Features
- Download Instagram profiles (images, videos, and metadata).
- Calculate and log the SHA1 hash for all `.jpg` and `.mp4` files.
- Intuitive and user-friendly GUI powered by Tkinter.
- Progress bar and logging for real-time feedback during downloads.
- Extensible and configurable.

## Prerequisites
1. **Python**: Make sure Python 3.8 or later is installed.
2. **Dependencies**:
    - `instaloader`
    - `tenacity`
    - `tqdm`
    - `tkinter` (default with Python on most platforms)

Install the required libraries using:
```bash
pip install instaloader tenacity tqdm
```

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/instagram-forensic-downloader.git
   cd instagram-forensic-downloader
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Use
1. Run the script:
   ```bash
   python instagram_downloader_gui.py
   ```
2. Enter the Instagram profile URL in the input field.
3. Click the **Download** button to start downloading.
4. View the progress and logs in the respective sections of the GUI.

## Hash Calculation
- The tool calculates the **SHA1** hash for all downloaded `.jpg` and `.mp4` files. The hash values are logged in the "Log" section of the GUI for verification purposes.

## Configuration
Settings can be customized in the `Config` class:
- Enable or disable specific download options (e.g., pictures, videos, comments).
- Adjust the chunk size, maximum workers, or retry attempts.

## Example
1. Input a valid Instagram profile URL:
   ```
   https://www.instagram.com/example_profile/
   ```
2. The tool will download the profile content and log the SHA1 hash for relevant files.

## Known Issues
- **Login Required**: Some profiles may require authentication.
  - Uncomment and configure the `loader.login` line in the `download_profile` method.
- **Tkinter Not Available**: Ensure Tkinter is installed if you encounter GUI-related errors.

## Contributing
Feel free to submit issues or pull requests to improve the tool. Contributions are always welcome!

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Disclaimer
This tool is intended for forensic and lawful use only. Ensure you have proper authorization before downloading content from Instagram.



