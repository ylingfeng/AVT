import os
import subprocess as sp
import sys
import time

from moviepy.editor import VideoFileClip
from pytube import YouTube


def download_youtube_id(vid, dest_path):
    youtube_video = 'https://www.youtube.com/watch?v=' + vid

    exec_command = [
        'yt-dlp',
        '-f',
        'bv+ba/b',
        youtube_video,
        '-o',
        dest_path + '/%(id)s.%(ext)s'
    ]
    print("exec commands: ", exec_command)
    p = sp.Popen(exec_command)
    p.wait()
    time.sleep(5)


def get_video_info(fn):
    youtube_id = os.path.basename(fn).split(".")[0]

    url = f"https://www.youtube.com/watch?v={youtube_id}"
    yt = YouTube(url)
    clip = VideoFileClip(fn)
    fps = clip.fps
    duration = clip.duration
    total_frames = int(fps * duration)
    minutes, seconds = divmod(int(duration), 60)
    hours, minutes = divmod(minutes, 60)
    length = f"{hours}:{minutes:02d}:{seconds:02d}"

    try:
        title = yt.title
    except:
        print(url)
        exit()
    frames = str(total_frames)

    video_info = {youtube_id: {
        "fps": fps,
        "frames": frames,
        "title": title,
        "url": url,
        "length": length,
        "anno": []
    }}

    return video_info


youtube_id = sys.argv[1]
path = f"/path/to/videos/{youtube_id}"

download_youtube_id(youtube_id, path)

info = get_video_info(path)
print(info)
