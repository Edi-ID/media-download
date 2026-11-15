# ==================================
# 1. IMPORT & SETUP AWAL
# ==================================
import os
import re
import glob
from urllib.parse import quote, unquote
from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import requests

app = Flask(__name__)
os.makedirs("downloads", exist_ok=True)

# ==================================
# 2. FUNGSI BANTU
# ==================================
def bersih_nama(nama):
    if not nama:
        return "video"

    # 1. Buang semua link (shopee, fb, http, httpss, dll)
    nama = re.sub(r'https+s?://\S+', '', nama, flags=re.IGNORECASE)
    nama = re.sub(r'https+s?\.?\S*shopee\S*', '', nama, flags=re.IGNORECASE)
    nama = re.sub(r'\b\w*shopee\.\S+', '', nama, flags=re.IGNORECASE)
    nama = re.sub(r'\b(?:https?|http|httpss|www)\S*', '', nama, flags=re.IGNORECASE)
    nama = re.sub(r'\b\S+\.(?:co\.id|com|id|net|org)\S*', '', nama, flags=re.IGNORECASE)

    # 2. Buang pola kotor di depan: "12K reactions · 22 shares" / "8.8K views · 836 reactions"
    for _ in range(3):
        baru = re.sub(
            r'^\s*[\d\.,KkMmB]+\s*(views?|reactions?|shares?|likes?|comments?)\s*[·•\|\-–]*\s*([\d\.,KkMmB]+\s*(views?|reactions?|shares?|likes?|comments?)\s*[·•\|\-–]*\s*)?',
            '',
            nama,
            flags=re.IGNORECASE
        )
        if baru == nama:
            break
        nama = baru

    # 3. Cadangan kalo masih ada sisa
    nama = re.sub(r'^\s*.*?reactions?\s*[·•\|\-–]*', '', nama, flags=re.IGNORECASE)
    nama = re.sub(r'^\s*.*?shares?\s*[·•\|\-–]*', '', nama, flags=re.IGNORECASE)

    # 4. Buang karakter terlarang & rapikan
    nama = re.sub(r'[\\/*?:"<>|]', '', nama)
    nama = re.sub(r'\s+', ' ', nama).strip()
    # INI YANG BIKIN ....mp4 ILANG: buang titik-titik di ujung judul
    nama = nama.rstrip('. ').strip()
    nama = re.sub(r'\.{2,}', '', nama).strip()
    return nama[:80].rstrip('. ').strip() or "video"

def get_opts(is_audio=False):
    opts = {
        'quiet': True,
        'no_warnings': True,
        # FIX: Pake ID aja biar gak jadi ....mp4
        'outtmpl': os.path.join("downloads", '%(id)s.%(ext)s'),
        # FIX: False biar gak jadi _.mp4 (huruf Thailand / emoji gak diubah jadi _)
        'restrictfilenames': False,
        'user_agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'socket_timeout': 30,
        'retries': 3,
    }
    if is_audio:
        # FIX FINAL: JANGAN pake FFmpegExtractAudio, itu biang ffmpeg not found
        # Langsung ambil audio terbaik (m4a), nanti di-rename jadi .mp3
        opts.update({
            'format': 'bestaudio[ext=m4a]/bestaudio/best'
        })
    else:
        # Video juga JANGAN pake remux / recode
        opts.update({'format': 'best[ext=mp4]/best'})
    return opts

def tiktok_via_tikwm(url):
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
            data['title'] = bersih_nama(data.get('title', ''))
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
                'title': bersih_nama(data.get('title', '')),
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
                return jsonify({'file': f"/file/{quote(os.path.basename(fn))}"})
        except Exception as e:
            print("TikTok download gagal:", e)

    try:
        with yt_dlp.YoutubeDL(get_opts(is_audio)) as ydl:
            data = ydl.extract_info(url, download=True)
            fn = ydl.prepare_filename(data)

            if is_audio:
                # File aslinya bisa .m4a / .webm / .opus, cari yang beneran ada
                base = os.path.splitext(fn)[0]
                fn_ketemu = None
                for ext_coba in ['.m4a', '.webm', '.mp3', '.opus', '.mp4']:
                    if os.path.exists(base + ext_coba):
                        fn_ketemu = base + ext_coba
                        break
                # Cadangan: cari pake glob kalo ID-nya beda
                if not fn_ketemu:
                    hasil = glob.glob(base + ".*")
                    if hasil:
                        fn_ketemu = hasil[0]
                if fn_ketemu:
                    fn = fn_ketemu

            # Paksa selalu .mp4 / .mp3 + RENAME file asli
            ext = '.mp3' if is_audio else '.mp4'
            nama_rapi = bersih_nama(data.get('title', 'video')) + ext

            path_baru = os.path.join("downloads", nama_rapi)
            try:
                if os.path.abspath(fn) != os.path.abspath(path_baru):
                    if os.path.exists(path_baru):
                        os.remove(path_baru)
                    os.rename(fn, path_baru)
                    fn = path_baru
            except Exception as e:
                print("Rename gagal:", e)

            # Jangan pake ?nama= lagi, langsung kirim nama file yang udah bersih
            return jsonify({'file': f"/file/{quote(os.path.basename(fn))}"})
    except Exception as e:
        return jsonify({'error': str(e)[:300]}), 400

@app.route('/file/<name>')
def serve_file(name):
    name = unquote(name)
    path = os.path.join("downloads", name)
    if name.lower().endswith('.mp3'):
        mimetype = 'audio/mpeg'
    else:
        mimetype = 'video/mp4'
    return send_file(path, as_attachment=True, download_name=name, mimetype=mimetype)

# ==================================
# 4. JALANKAN SERVER
# ==================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
