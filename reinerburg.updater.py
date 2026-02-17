import os
import threading
import requests
import zipfile
import customtkinter as ctk
from packaging import version

# ----------------------------
# CONFIG
# ----------------------------

API_URL = "https://git.ryujinx.app/api/v4/projects/ryubing%2Fryujinx/releases"
LOCAL_VERSION_FILE = "version.txt"
DOWNLOAD_NAME = "ryujinx_source.zip"

# Dracula Colors
BG = "#282a36"
CARD = "#1e1f29"
PURPLE = "#bd93f9"
CYAN = "#8be9fd"
GREEN = "#50fa7b"
RED = "#ff5555"
TEXT = "#f8f8f2"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ----------------------------
# RELEASE CHECK
# ----------------------------

def get_latest_release():
    response = requests.get(API_URL, timeout=15)
    response.raise_for_status()

    latest = response.json()[0]
    tag = latest["tag_name"]

    zip_url = None
    for asset in latest["assets"]["sources"]:
        if asset["format"] == "zip":
            zip_url = asset["url"]
            break

    if not zip_url:
        raise Exception("No source zip found.")

    return tag, zip_url


def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        return None
    with open(LOCAL_VERSION_FILE, "r") as f:
        return f.read().strip()


def save_local_version(ver):
    with open(LOCAL_VERSION_FILE, "w") as f:
        f.write(ver)


def update_available(local, remote):
    if not local:
        return True
    try:
        return version.parse(remote) > version.parse(local)
    except:
        return remote != local


# ----------------------------
# DOWNLOAD
# ----------------------------

def download_file(url, progress_callback):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0

        with open(DOWNLOAD_NAME, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total:
                        percent = downloaded / total
                        progress_callback(percent)

    return DOWNLOAD_NAME


def extract_zip(path):
    extract_folder = "Sources"

    with zipfile.ZipFile(path, "r") as zip_ref:
        zip_ref.extractall(extract_folder)


# ----------------------------
# GUI
# ----------------------------

class Updater(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Reinerburg Updater")
        self.geometry("500x260")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        # Card Frame
        self.card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=15)
        self.card.pack(padx=20, pady=20, fill="both", expand=True)

        self.title_label = ctk.CTkLabel(
            self.card,
            text="Ryujinx Source Updater",
            font=("Segoe UI", 20, "bold"),
            text_color=PURPLE
        )
        self.title_label.pack(pady=(15, 5))

        self.status_label = ctk.CTkLabel(
            self.card,
            text="Ready to check for updates",
            text_color=TEXT
        )
        self.status_label.pack(pady=5)

        self.progress = ctk.CTkProgressBar(
            self.card,
            width=380,
            progress_color=CYAN
        )
        self.progress.set(0)
        self.progress.pack(pady=15)

        self.button = ctk.CTkButton(
            self.card,
            text="Check for Updates",
            fg_color=PURPLE,
            hover_color="#a277ff",
            text_color="black",
            command=self.start_thread
        )
        self.button.pack(pady=10)

    def start_thread(self):
        self.button.configure(state="disabled")
        threading.Thread(target=self.run_update, daemon=True).start()

    def set_progress(self, value):
        self.progress.set(value)
        self.update_idletasks()

    def run_update(self):
        try:
            self.status_label.configure(text="Checking latest release...")

            remote_version, zip_url = get_latest_release()
            local_version = get_local_version()

            if not update_available(local_version, remote_version):
                self.status_label.configure(
                    text="Already up to date ✔",
                    text_color=GREEN
                )
                return

            self.status_label.configure(text="Downloading update...")
            zip_path = download_file(zip_url, self.set_progress)

            self.status_label.configure(text="Extracting files...")
            extract_zip(zip_path)

            # Delete ZIP after successful extraction
            if os.path.exists(zip_path):
                os.remove(zip_path)

            save_local_version(remote_version)

            self.status_label.configure(
                text="Update completed successfully ✔",
                text_color=GREEN
            )

        except Exception as e:
            self.status_label.configure(
                text=f"Error: {str(e)}",
                text_color=RED
            )

        finally:
            self.progress.set(0)
            self.button.configure(state="normal")


# ----------------------------
# MAIN
# ----------------------------

if __name__ == "__main__":
    app = Updater()
    app.mainloop()