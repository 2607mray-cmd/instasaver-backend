from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
import urllib.parse
import re
import sys
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/info")
async def get_video_info(data: dict = Body(...)):
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android']
                }
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = info.get('formats', [])
            # Filter for mp4 formats with audio/video to avoid complex merging for streaming
            valid_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4']
            
            # Identify 'Normal' (~360p-480p) and 'HD' (720p+)
            normal = next((f for f in valid_formats if f.get('height') and 360 <= f.get('height') <= 480), None)
            hd = next((f for f in reversed(valid_formats) if f.get('height') and f.get('height') >= 720), None)
            
            # Fallback
            if not hd and valid_formats:
                hd = valid_formats[-1] # Best available
            if not normal and valid_formats:
                normal = valid_formats[0] # Worst available

            # Helper to get size
            def get_size(f):
                return f.get('filesize') or f.get('filesize_approx') or (
                    (f.get('tbr') or ((f.get('vbr') or 0) + (f.get('abr') or 0))) * (info.get('duration') or 0) * 125 
                    if f.get('tbr') or f.get('vbr') or info.get('duration') else None
                )

            options = []
            if normal:
                options.append({
                    "label": f"Normal ({normal.get('resolution', '360p')})",
                    "id": normal['format_id'],
                    "filesize": get_size(normal)
                })
            if hd and hd['format_id'] != (normal['format_id'] if normal else None):
                options.append({
                    "label": f"HD ({hd.get('resolution', '720p')})",
                    "id": hd['format_id'],
                    "filesize": get_size(hd)
                })

            return {
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "description": info.get('description'),
                "tags": info.get('tags'),
                "options": options
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def download_video(url: str, format_id: str, title: str, filesize: float = None):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    cmd_stream = [sys.executable, "-m", "yt_dlp", "-o", "-", "-f", format_id, url]

    def iterfile():
        # Open subprocess
        with subprocess.Popen(cmd_stream, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**7) as sp:
             # Yield chunks of data
            while True:
                chunk = sp.stdout.read(64 * 1024) # 64KB chunks
                if not chunk:
                    break
                yield chunk

    # Headers for file download
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{urllib.parse.quote(title)}.mp4" # We filtered for mp4
    }
    if filesize:
        headers["Content-Length"] = str(int(filesize))

    return StreamingResponse(
        iterfile(), 
        media_type="video/mp4", 
        headers=headers
    )

@app.get("/")
def read_root():
    return {"Hello": "World"}

