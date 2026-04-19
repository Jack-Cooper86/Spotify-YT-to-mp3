chat i slightly done goofed please js download the sourcecode.zip file and unzip it im too lazy to figure out how to put that in the binaries tab ^^

# Spotify-YT-to-mp3
Simple Spotify/YT to mp3 converter depending on YT DLP (command line tool).


Setup - 

1. Open the file and fill in your credentials at line 14: [this is only available to spotify premium
subscribers]

   SPOTIFY_CLIENT_ID     = "your_client_id"
   SPOTIFY_CLIENT_SECRET = "your_client_secret"

2. Install yt-dlp
3. Install ffmpeg and add its `bin` folder to your system PATH.

Dependencies - 

- **Python 3** — [python.org](https://python.org)
- **yt-dlp** — `pip install yt-dlp`
- **ffmpeg** — [ffmpeg.org](https://ffmpeg.org/download.html), must be added to PATH
- **Spotify Developer credentials** — free at [developer.spotify.com](https://developer.spotify.com/dashboard)

How to run - 

In command line:
C: (or whatever drive you've saved the file in)

python spotify_to_mp3.py

Paste any Spotify track URL → hit **Download MP3** → file saves as `Artist - Song.mp3`




