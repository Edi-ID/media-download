# ==================================
# 1. IMPORT & SETUP AWAL
# ==================================
import os
import re
from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import requests

app = Flask(__name__)
os.makedirs("downloads", exist_ok=True)

# ==================================
# 2. FUNGSI BANTU
# ==================================
def bersih_nama(nama):
    # Buang karakter yang gak boleh buat nama file
    nama = re.sub(r'[\\/*?:"<>|]', '', nama)
    return nama[:80].strip() or "video"

def get_opts(is_audio=False):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join("downloads", '%(title).80s.%(ext)s'),
        'restrictfilenames': True,
        'user_agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'socket_timeout': 30,
        'retries': 3,
    }
    if is_audio:
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        })
    else:
        opts.update({'format': 'best[ext=mp4]/best'})
    return opts

def tiktok_via_tikwm(url):
    # TikTok pake API TikWM biar lebih stabil
    try:
        r = requests.get("https://www.tikwm.com/api/", params={"url": url}, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        j = r.json()
        if j.get("code") == 0 and j.get("data"):
            d = j["data"]
            return {
                'title': d.get("title", "TikTok Video"),
                'thumbnail': d.get("cover", ""),
                'uploader': d.get("author", {}).get("nickname", "@tiktok"),
                'video_url': d.get("play", "") or d.get("wmplay", ""),
                'tiktok_direct': d.get("play", "")
            }
    except Exception as e:
        print("TikWM gagal:", e)
    return None

# ==================================
# 3. ROUTE / HALAMAN
# ==================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info', methods=['POST'])
def info():
    url = request.json.get('url', '')

    if "youtube.com" in url or "youtu.be" in url:
        return jsonify({'error': 'YouTube Sudah dihapus, soalnya sering kena blok. Pake TikTok / IG / FB aja!'}), 400

    if "tiktok.com" in url or "vt.tiktok" in url:
        data = tiktok_via_tikwm(url)
        if data:
            return jsonify(data)

    try:
        with yt_dlp.YoutubeDL(get_opts()) as ydl:
            data = ydl.extract_info(url, download=False)
            video_url = data.get('url', '')
            if not video_url and data.get('formats'):
                for f in reversed(data.get('formats', [])):
                    if f.get('ext') == 'mp4' and f.get('url'):
                        video_url = f.get('url')
                        break
            return jsonify({
                'title': data.get('title', ''),
                'thumbnail': data.get('thumbnail', ''),
                'uploader': data.get('uploader', ''),
                'video_url': video_url
            })
    except Exception as e:
        return jsonify({'error': str(e)[:250]}), 400

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url', '')
    is_audio = request.json.get('audio', False)

    if "youtube.com" in url or "youtu.be" in url:
        return jsonify({'error': 'YouTube udah dihapus!'}), 400

    if ("tiktok.com" in url or "vt.tiktok" in url) and not is_audio:
        try:
            d = tiktok_via_tikwm(url)
            if d and d.get("tiktok_direct"):
                r = requests.get(d["tiktok_direct"], headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                fn = os.path.join("downloads", bersih_nama(d["title"]) + ".mp4")
                with open(fn, "wb") as f:
                    f.write(r.content)
                return jsonify({'file': f"/file/{os.path.basename(fn)}?nama={os.path.basename(fn)}"})
        except Exception as e:
            print("TikTok download gagal:", e)

    try:
        with yt_dlp.YoutubeDL(get_opts(is_audio)) as ydl:
            data = ydl.extract_info(url, download=True)
            fn = ydl.prepare_filename(data)
            if is_audio:
                fn = os.path.splitext(fn)[0] + '.mp3'
            nama_rapi = bersih_nama(data.get('title', 'video')) + os.path.splitext(fn)[1]
            return jsonify({'file': f"/file/{os.path.basename(fn)}?nama={nama_rapi}"})
    except Exception as e:
        return jsonify({'error': str(e)[:300]}), 400

@app.route('/file/<name>')
def serve_file(name):
    nama = request.args.get('nama', name)
    return send_file(os.path.join("downloads", name), as_attachment=True, download_name=nama)

# ==================================
# 4. JALANKAN SERVER
# ==================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)