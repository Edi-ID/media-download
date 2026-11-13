from flask import Flask, request, jsonify, send_file
import yt_dlp
import os, re, requests

app = Flask(__name__)
os.makedirs("downloads", exist_ok=True)

HTML = """<!DOCTYPE html>
<html lang="id" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>All Downloader</title>
<style>
  :root {
    --bg: #f2f4f8;
    --card: rgba(255, 255, 255, 0.75);
    --text: #0c1222;
    --muted: #5f6c89;
    --accent: #007BFF;
    --accent2: #0056b3;
    --shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  }
  [data-theme="dark"] {
    --bg: #050b17;
    --card: rgba(16, 24, 42, 0.55);
    --text: #e8efff;
    --muted: #9fb7dd;
    --accent: #4f8bff;
    --accent2: #82afff;
    --shadow: 0 8px 25px rgba(0, 0, 0, 0.35);
  }
    * { box-sizing: border-box; font-family: "Inter", system-ui, Roboto, Arial, sans-serif; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    -webkit-user-select: none; user-select: none;
    min-height: 100vh; display: flex; flex-direction: column;
    padding-bottom: 90px; text-align: center;
    background-image: url('https://raw.githubusercontent.com/garsella7/garsella7.github.io/refs/heads/main/image/1794559685-picsay.jpg');
    background-size: cover; background-position: center;
    background-attachment: fixed; background-repeat: no-repeat;
    animation: zoomBg 20s ease-in-out infinite alternate;
  }
  @keyframes zoomBg { from { background-size: 100% auto; } to { background-size: 110% auto; } }
  body::before { content: ""; position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: -1; }
  html[data-theme="light"] body::before { background: rgba(255,255,255,0.35); }
  .container { max-width: 500px; margin: 0 auto; padding: 22px 14px 40px; width: 100%; text-align: center; animation: naik 0.6s ease; }
  @keyframes naik { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
  .topbar { display: flex; justify-content: space-between; align-items: center; max-width: 500px; width: 100%; margin: 0 auto; padding: 14px 8px 14px 16px; }
  .logo { font-weight: 800; font-size: 18px; text-align: left; flex: 1; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }
  html[data-theme="light"] .logo { text-shadow: none; }
  #tema { border: none; background: var(--card); color: var(--text); font-size: 20px; padding: 8px 12px; border-radius: 50%; cursor: pointer; box-shadow: var(--shadow); backdrop-filter: blur(10px); flex-shrink: 0; margin-left: auto; margin-right: 0; transition: transform 0.2s; }
  #tema:active { transform: scale(0.85) rotate(20deg); }
  .box { background: var(--card); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); padding: 22px; border-radius: 22px; width: 100%; margin: 12px auto 0 auto; box-shadow: var(--shadow); border: 1px solid rgba(255,255,255,0.25); text-align: center; }
  p.sub { margin: 12px 0 0; font-size: 16px; font-weight: 700; text-align: center; display: inline-block; padding: 7px 16px; border-radius: 50px; }
  html[data-theme="light"] p.sub { color: #0c1222; background: rgba(255,255,255,0.85); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
  html[data-theme="dark"] p.sub { color: #fff; background: rgba(0,0,0,0.40); backdrop-filter: blur(8px); text-shadow: 0 1px 4px rgba(0,0,0,0.5); }
  .input-row { display: flex; gap: 8px; align-items: center; margin: 12px 0; }
  input { flex: 1; padding: 13px 14px; border-radius: 12px; border: 1px solid rgba(128,128,128,0.3); font-size: 15px; outline: none; background: rgba(255,255,255,0.95); color: #111; text-align: center; }
  input:focus { border-color: #007BFF; box-shadow: 0 0 0 3px rgba(0,123,255,0.25); }
  .btn-paste { padding: 13px 14px; border-radius: 12px; background: #fff; color: #111; font-size: 16px; flex-shrink: 0; margin: 0; }
  .btn-paste:hover { background: #eee; }
  /* TOMBOL UTAMA - GRADIENT + PULSE KEREN */
  .btn-utama {
    width: 100%; padding: 15px 22px; border: none; border-radius: 14px;
    background: linear-gradient(135deg, #007BFF, #00C6FF, #7B61FF);
    background-size: 200% 200%; color: #fff; font-weight: 800; cursor: pointer;
    margin: 8px auto; font-size: 16px; box-shadow: 0 8px 20px rgba(0,123,255,0.4);
    animation: gradasi 3s ease infinite, pulse 2s ease-in-out infinite;
  }
  @keyframes gradasi { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
  @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.03)} }
  .btn-utama:active { transform: scale(0.97); }
  button { padding: 13px 22px; border: none; border-radius: 12px; background: var(--accent); color: #fff; font-weight: 700; cursor: pointer; margin: 5px auto; font-size: 15px; transition: transform 0.15s; }
  button:hover { transform: translateY(-2px); }
  button.green { background: linear-gradient(135deg, #25D366, #128C7E); }
  img, video { max-width: 100%; border-radius: 12px; margin-top: 12px; }
  video { width: 100%; background: #000; }
  #hasil h3 { animation: naik 0.4s ease; }
  footer { position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%); background: var(--card); backdrop-filter: blur(10px); padding: 10px 22px; font-size: 13px; color: var(--muted); border-radius: 50px; box-shadow: var(--shadow); white-space: nowrap; z-index: 99; }
  footer b { color: var(--text); font-size: 14px; }
</style>
</head>
<body>
  <div class="topbar">
    <div class="logo">Sosial Media Downloader</div>
    <button id="tema" onclick="gantiTema()">🌙</button>
  </div>
  <div class="container">
    <p class="sub">TikTok ✅ Instagram ✅ Facebook ✅</p>
    <div class="box">
      <div class="input-row">
        <input id="url" placeholder="Masukkan Link disini...">
        <button class="btn-paste" onclick="pasteLink()" title="Paste Link">📋</button>
      </div>
      <button class="btn-utama" onclick="cek()">⬇️ Download Video MP4/MP3</button>
      <div id="hasil"></div>
    </div>
  </div>
  <footer>Created By: <b>@idgarsell</b> ✨</footer>
<script>
  const saved = localStorage.getItem('tema') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  document.getElementById('tema').innerText = saved === 'dark' ? '🌙' : '☀️';
  function gantiTema(){
    const html = document.documentElement;
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    document.getElementById('tema').innerText = next === 'dark' ? '🌙' : '☀️';
    localStorage.setItem('tema', next);
  }
  async function pasteLink(){
    try{
      const text = await navigator.clipboard.readText();
      if(text){ document.getElementById('url').value = text; cek(); }
      else alert('Copy dulu link-nya');
    }catch(e){ alert('izin clipboard belum dikasih, paste manual Aja'); }
  }
  async function cek(){
    let url = document.getElementById('url').value;
    if(url.includes('youtube.com') || url.includes('youtu.be')){
      return document.getElementById('hasil').innerHTML = '<p style="color:orange">⚠️ YouTube udah dihapus, soalnya sering kena blok. Pake TikTok / IG / FB aja ya!</p>';
    }
    document.getElementById('hasil').innerHTML = '<p>⏳ Harap Tunggu Bentar... 🔥</p>';
    let r = await fetch('/info', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({url})});
    let d = await r.json();
    if(d.error) return document.getElementById('hasil').innerHTML = '<p style="color:red">'+d.error+'</p>';
    let player = d.video_url ? `<video controls playsinline src="${d.video_url}" poster="${d.thumbnail}"></video>` : `<img src="${d.thumbnail}">`;
    document.getElementById('hasil').innerHTML = player + `<h3>${d.title}</h3><p>${d.uploader}</p><button class="green" onclick="dl(false)">⬇️ VIDEO</button><button onclick="dl(true)">🎵 MP3</button>`;
  }
  async function dl(audio){
    let url = document.getElementById('url').value;
    let r = await fetch('/download', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({url, audio})});
    let d = await r.json();
    if(d.error) return alert(d.error);
    window.location.href = d.file;
  }
</script>
</body>
</html>"""

def bersih_nama(nama):
    nama = re.sub(r'[\\/*?:"<>|]', '', nama)
    return nama[:80].strip() or "video"

def get_opts(is_audio=False):
    opts = {
        'quiet': True, 'no_warnings': True,
        'outtmpl': os.path.join("downloads", '%(title).80s.%(ext)s'),
        'restrictfilenames': True,
        'user_agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'socket_timeout': 30, 'retries': 3,
    }
    if is_audio:
        opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]})
    else:
        opts.update({'format': 'best[ext=mp4]/best'})
    return opts

def tiktok_via_tikwm(url):
    try:
        r = requests.get("https://www.tikwm.com/api/", params={"url": url}, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        j = r.json()
        if j.get("code") == 0 and j.get("data"):
            d = j["data"]
            return {'title': d.get("title", "TikTok Video"), 'thumbnail': d.get("cover", ""), 'uploader': d.get("author", {}).get("nickname", "@tiktok"), 'video_url': d.get("play", "") or d.get("wmplay", ""), 'tiktok_direct': d.get("play", "")}
    except Exception as e:
        print("TikWM gagal:", e)
    return None

@app.route('/')
def index():
    return HTML

@app.route('/info', methods=['POST'])
def info():
    url = request.json.get('url', '')
    if "youtube.com" in url or "youtu.be" in url:
        return jsonify({'error': 'YouTube Sudah dihapus, soalnya sering kena blok. Pake TikTok / IG / FB aja!'}), 400
    if "tiktok.com" in url or "vt.tiktok" in url:
        data = tiktok_via_tikwm(url)
        if data: return jsonify(data)
    try:
        with yt_dlp.YoutubeDL(get_opts()) as ydl:
            data = ydl.extract_info(url, download=False)
            video_url = data.get('url', '')
            if not video_url and data.get('formats'):
                for f in reversed(data.get('formats', [])):
                    if f.get('ext') == 'mp4' and f.get('url'):
                        video_url = f.get('url'); break
            return jsonify({'title': data.get('title', ''), 'thumbnail': data.get('thumbnail', ''), 'uploader': data.get('uploader', ''), 'video_url': video_url})
    except Exception as e:
        return jsonify({'error': str(e)[:250]}), 400

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url', ''); is_audio = request.json.get('audio', False)
    if "youtube.com" in url or "youtu.be" in url:
        return jsonify({'error': 'YouTube udah dihapus!'}), 400
    if ("tiktok.com" in url or "vt.tiktok" in url) and not is_audio:
        try:
            d = tiktok_via_tikwm(url)
            if d and d.get("tiktok_direct"):
                r = requests.get(d["tiktok_direct"], headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                fn = os.path.join("downloads", bersih_nama(d["title"]) + ".mp4")
                with open(fn, "wb") as f: f.write(r.content)
                return jsonify({'file': f"/file/{os.path.basename(fn)}?nama={os.path.basename(fn)}"})
        except Exception as e:
            print("TikTok download gagal:", e)
    try:
        with yt_dlp.YoutubeDL(get_opts(is_audio)) as ydl:
            data = ydl.extract_info(url, download=True)
            fn = ydl.prepare_filename(data)
            if is_audio: fn = os.path.splitext(fn)[0] + '.mp3'
            nama_rapi = bersih_nama(data.get('title', 'video')) + os.path.splitext(fn)[1]
            return jsonify({'file': f"/file/{os.path.basename(fn)}?nama={nama_rapi}"})
    except Exception as e:
        return jsonify({'error': str(e)[:300]}), 400

@app.route('/file/<name>')
def serve_file(name):
    nama = request.args.get('nama', name)
    return send_file(os.path.join("downloads", name), as_attachment=True, download_name=nama)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
