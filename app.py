from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import threading
import uuid
import shutil
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'darkx-video-downloader-secret'

# Folda za kuhifadhi faili
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Kuhifadhi progress za downloads
download_progress = {}

def progress_hook(d):
    if d['status'] == 'downloading':
        download_id = d['info_dict']['_download_id']
        if 'total_bytes' in d:
            total = d['total_bytes']
            downloaded = d['downloaded_bytes']
            percent = (downloaded / total) * 100
        elif 'total_bytes_estimate' in d:
            total = d['total_bytes_estimate']
            downloaded = d['downloaded_bytes']
            percent = (downloaded / total) * 100
        else:
            percent = 0
        
        download_progress[download_id] = {
            'percent': round(percent, 1),
            'speed': d.get('speed', 0),
            'eta': d.get('eta', 0),
            'status': 'downloading'
        }
    elif d['status'] == 'finished':
        download_id = d['info_dict']['_download_id']
        download_progress[download_id] = {
            'percent': 100,
            'status': 'finished',
            'filename': d['filename']
        }

def download_video(url, quality, format_type, download_id):
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
        '_download_id': download_id
    }
    
    if format_type == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'embedthumbnail': True,
            'addmetadata': True,
        })
    else:
        if quality == '2160p':
            format_spec = 'bestvideo[height<=2160]+bestaudio/best[height<=2160]'
        elif quality == '1080p':
            format_spec = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif quality == '720p':
            format_spec = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif quality == '480p':
            format_spec = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
        else:
            format_spec = 'best'
        
        ydl_opts.update({
            'format': format_spec,
            'merge_output_format': format_type,
        })
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Adjust filename for MP3
            if format_type == 'mp3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            download_progress[download_id]['filename'] = filename
            download_progress[download_id]['status'] = 'completed'
            
    except Exception as e:
        download_progress[download_id] = {
            'status': 'error',
            'error': str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'formats': [
                    {
                        'format_id': f.get('format_id'),
                        'quality': f.get('height', 'Audio') if f.get('height') else 'Audio',
                        'ext': f.get('ext', '')
                    }
                    for f in info.get('formats', [])
                    if f.get('height') or f.get('acodec') != 'none'
                ][:10]
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download', methods=['POST'])
def start_download():
    url = request.json.get('url')
    quality = request.json.get('quality', '720p')
    format_type = request.json.get('format', 'mp4')
    
    download_id = str(uuid.uuid4())
    
    download_progress[download_id] = {
        'status': 'starting',
        'percent': 0
    }
    
    thread = threading.Thread(
        target=download_video,
        args=(url, quality, format_type, download_id)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'download_id': download_id})

@app.route('/api/progress/<download_id>')
def get_progress(download_id):
    if download_id in download_progress:
        return jsonify(download_progress[download_id])
    return jsonify({'status': 'not_found'})

@app.route('/api/download-file/<path:filename>')
def download_file(filename):
    return send_file(
        os.path.join(DOWNLOAD_FOLDER, filename),
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """Cleanup old files after download"""
    try:
        shutil.rmtree(DOWNLOAD_FOLDER)
        os.makedirs(DOWNLOAD_FOLDER)
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
