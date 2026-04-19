import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import re
import os
import subprocess
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import base64
import time

SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""


def get_spotify_token():
    creds = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    encoded = base64.b64encode(creds.encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={"Authorization": f"Basic {encoded}", "Content-Type": "application/x-www-form-urlencoded"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["access_token"]

def get_playlist_tracks(playlist_id, token):
    tracks = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=100"
    while url:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
            for item in data['items']:
                if item['track']:
                    t = item['track']
                    tracks.append((t['name'], ", ".join(a['name'] for a in t['artists'])))
            url = data.get('next')
    return tracks

def get_track_info(track_id, token):
    req = urllib.request.Request(
        f"https://api.spotify.com/v1/tracks/{track_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    return data["name"], ", ".join(a["name"] for a in data["artists"])

def get_search_results(query):
    cmd = [
        sys.executable, "-m", "yt_dlp",
        f"ytsearch10:{query}",
        "--dump-json",
        "--flat-playlist",
        "--no-warnings"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    results = []
    for line in result.stdout.splitlines():
        try:
            entry = json.loads(line)
            results.append({
                "title": entry.get("title"),
                "url": entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}",
                "duration": entry.get("duration_string", "??:??")
            })
        except:
            continue
    return results


class SelectionWindow(tk.Toplevel):
    def __init__(self, parent, results):
        super().__init__(parent)
        self.title("Select Correct Version")
        self.geometry("500x400")
        self.configure(bg="#111111")
        self.result_url = None

        tk.Label(self, text="Select the best match:", font=("Helvetica Neue", 12, "bold"),
                 fg="#1DB954", bg="#111111", pady=10).pack()

        self.listbox = tk.Listbox(self, bg="#0A0A0A", fg="#FFFFFF", font=("Helvetica Neue", 10),
                                  selectbackground="#1DB954", bd=0, highlightthickness=0)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=5)

        for res in results:
            self.listbox.insert("end", f"[{res['duration']}] {res['title']}")

        btn = tk.Button(self, text="Download Selected", bg="#1DB954", fg="#0A0A0A",
                        font=("Helvetica Neue", 10, "bold"), command=self._on_select, pady=8)
        btn.pack(fill="x", padx=20, pady=15)

        self.results = results
        self.grab_set()
        self.wait_window()

    def _on_select(self):
        idx = self.listbox.curselection()
        if idx:
            self.result_url = self.results[idx[0]]["url"]
            self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spotify → MP3")
        self.resizable(False, False)
        self.configure(bg="#0A0A0A")
        self.output_dir = os.path.expanduser("~/Downloads")
        self._build_ui()

    def _build_ui(self):
        BG, CARD, GREEN, WHITE, MUTED, BORDER = "#0A0A0A", "#111111", "#1DB954", "#FFFFFF", "#888888", "#222222"
        FONT_H, FONT_B, FONT_S = ("Helvetica Neue", 22, "bold"), ("Helvetica Neue", 12), ("Helvetica Neue", 10)

        outer = tk.Frame(self, bg=BG, padx=32, pady=32)
        outer.pack()

        tk.Label(outer, text="Spotify / YT → MP3", font=FONT_H, fg=GREEN, bg=BG).pack(anchor="w")
        tk.Label(outer, text="Supports Tracks, Playlists, and YouTube links.", font=FONT_S, fg=MUTED, bg=BG).pack(anchor="w", pady=(2, 20))

        card = tk.Frame(outer, bg=CARD, bd=0, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", pady=(0, 12))

        tk.Label(card, text="Spotify or YouTube URL", font=FONT_S, fg=MUTED, bg=CARD).pack(anchor="w", padx=14, pady=(12, 2))
        self.url_var = tk.StringVar()
        entry = tk.Entry(card, textvariable=self.url_var, font=FONT_B, fg=WHITE, bg=CARD, bd=0, insertbackground=WHITE, width=52)
        entry.pack(anchor="w", padx=14, pady=(0, 12))

        folder_row = tk.Frame(outer, bg=BG)
        folder_row.pack(fill="x", pady=(0, 16))
        self.folder_label = tk.Label(folder_row, text=f"📁  {self.output_dir}", font=FONT_S, fg=MUTED, bg=BG, anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True)
        tk.Button(folder_row, text="Change", font=FONT_S, fg=MUTED, bg=CARD, bd=0, command=self._pick_folder).pack(side="right")

        self.dl_btn = tk.Button(outer, text="Download MP3", font=("Helvetica Neue", 13, "bold"), fg=BG, bg=GREEN, bd=0, pady=12, command=self._start_download)
        self.dl_btn.pack(fill="x", pady=(0, 16))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("G.Horizontal.TProgressbar", troughcolor=CARD, background=GREEN, thickness=4)
        self.progress = ttk.Progressbar(outer, style="G.Horizontal.TProgressbar", mode="indeterminate", length=440)
        self.progress.pack(fill="x", pady=(0, 12))

        self.log_box = tk.Text(tk.Frame(outer, bg=CARD, bd=0, highlightthickness=1, highlightbackground=BORDER),
                               height=7, font=("Courier", 10), fg="#AAAAAA", bg=CARD, bd=0, state="disabled", wrap="word", padx=12, pady=10)
        self.log_box.master.pack(fill="x")

    def _pick_folder(self):
        d = filedialog.askdirectory(initialdir=self.output_dir)
        if d:
            self.output_dir = d
            self.folder_label.config(text=f"📁  {d if len(d) < 50 else '…'+d[-47:]}")

    def _log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            return
        self.dl_btn.config(state="disabled")
        self.progress.start(12)
        threading.Thread(target=self._download_logic, args=(url,), daemon=True).start()

    def _download_logic(self, url):
        try:
            if "youtube.com" in url or "youtu.be" in url:
                self._log(f"🎬 YouTube link detected...")
                self._run_ytdlp(url, self.output_dir)

            elif "spotify.com" in url:
                token = get_spotify_token()

                if "playlist/" in url:
                    p_id = re.search(r"playlist/([A-Za-z0-9]+)", url).group(1)
                    tracks = get_playlist_tracks(p_id, token)
                    p_dir = os.path.join(self.output_dir, f"Spotify_Playlist_{p_id[:6]}")
                    os.makedirs(p_dir, exist_ok=True)
                    self._log(f"📚 Downloading playlist ({len(tracks)} tracks)...")
                    for title, artist in tracks:
                        self._log(f"🎵 {artist} - {title}")
                        self._run_ytdlp(f"ytsearch1:{artist} - {title} audio", p_dir)

                elif "track/" in url:
                    t_id = re.search(r"track/([A-Za-z0-9]+)", url).group(1)
                    title, artist = get_track_info(t_id, token)
                    self._log(f"🔍 Searching options for: {artist} - {title}")
                    results = get_search_results(f"{artist} - {title} audio")

                    self.selected_url = None
                    self.after(0, lambda: self._open_selector(results))
                    while self.selected_url is None:
                        time.sleep(0.1)
                        if getattr(self, 'selector_closed', False):
                            break

                    if self.selected_url:
                        self._run_ytdlp(self.selected_url, self.output_dir)

            self._log("\n✨ Process Finished.")
        except Exception as e:
            self._log(f"\n❌ Error: {e}")
        finally:
            self.progress.stop()
            self.dl_btn.config(state="normal")

    def _open_selector(self, results):
        self.selector_closed = False
        sw = SelectionWindow(self, results)
        self.selected_url = sw.result_url
        self.selector_closed = True

    def _run_ytdlp(self, target, out_path):
        cmd = [
            sys.executable, "-m", "yt_dlp", target,
            "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0",
            "--output", os.path.join(out_path, "%(title)s.%(ext)s"),
            "--no-playlist", "--no-warnings"
        ]
        subprocess.run(cmd, capture_output=True)
        self._log(f"✅ Downloaded to folder: {os.path.basename(out_path)}")


if __name__ == "__main__":
    App().mainloop()
