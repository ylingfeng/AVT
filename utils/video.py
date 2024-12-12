import random

import cv2

from moviepy.editor import VideoFileClip
import random


def read_frames(video_path, section, sample_rate, sample_type=None, sample_size=None):
    # Load video using moviepy
    video_clip = VideoFileClip(video_path)
    fps = video_clip.fps
    frame_count = int(video_clip.duration * fps)
    width, height = video_clip.size

    video_info = dict(
        width=width,
        height=height,
        frame_count=frame_count,
        fps=fps,
    )

    if section is None:
        start_time = 0
        end_time = video_clip.duration
    else:
        start_time = section['start'] / fps
        end_time = section['end'] / fps
        start_time = max(start_time, 0)
        end_time = min(end_time, video_clip.duration)

    if sample_type is None:
        sample_interval = int(round(fps / sample_rate))
        sample_interval = max(sample_interval, 1)
        sample_id_list = list(range(int(start_time * fps), int(end_time * fps), sample_interval))
    elif sample_type == "uniform":
        sample_interval = int(frame_count / sample_size)
        sample_interval = max(sample_interval, 1)
        sample_id_list = list(range(int(start_time * fps), int(end_time * fps), sample_interval))
    elif sample_type == "random":
        sample_id_list = random.sample(range(int(end_time * fps)), sample_size)
    else:
        raise NotImplementedError

    # Extract frames based on sample_id_list
    frame_list = []
    for sample_id in sample_id_list:
        time = sample_id / fps
        if time > video_clip.duration:
            print(f'Skipping frame at {sample_id} (out of range)')
            break
        frame = video_clip.get_frame(time)
        frame_list.append(frame)

    video_clip.close()
    return frame_list, sample_id_list, video_info


def read_frames_cv2(video_path, section, sample_rate, sample_type=None, sample_size=None):
    video_capture = cv2.VideoCapture(video_path)

    if not video_capture.isOpened():
        print(f'read video {video_path} fail')
        return [], [], None

    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video_capture.get(cv2.CAP_PROP_FPS)

    video_info = dict(
        width=width,
        height=height,
        frame_count=frame_count,
        fps=fps,
    )

    if section is None:
        start = 0
        end = frame_count
    else:
        start, end = section['start'], section['end']
        start = max(start, 0)
        end = min(end, frame_count)

    if sample_type is None:
        sample_interval = int(round(fps / sample_rate))
        sample_interval = max(sample_interval, 1)
        sample_id_list = list(range(start, end, sample_interval))
    elif sample_type == "uniform":
        sample_interval = int(frame_count / sample_size)
        sample_interval = max(sample_interval, 1)
        sample_id_list = list(range(start, end, sample_interval))
    elif sample_type == "random":
        sample_id_list = random.sample(range(end), sample_size)
    else:
        raise NotImplementedError

    frame_list = []
    for sample_id in sample_id_list:
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, sample_id)

        ret, frame = video_capture.read()
        if not ret:
            print(f'read frame {sample_id} fail')
            break

        frame_list.append(frame)

    return frame_list, sample_id_list, video_info
