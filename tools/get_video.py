import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.pop(0)
sys.path.insert(0, '.')

import ffmpeg
import yaml
from moviepy.editor import (CompositeVideoClip, TextClip, VideoFileClip,
                            concatenate_videoclips)
from tqdm import tqdm

from utils.color_print import GREEN, PURPLE, UNSET, YELLOW
from utils.misc import get_path_info_list, get_video_path_list


def print_duration(total_duration_seconds):
    hours, remainder = divmod(total_duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"selected {total_duration_seconds:.2f} seconds, equals to {int(hours):02}:{int(minutes):02}:{seconds:05.2f}")


def merge_intervals(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = []

    for interval in intervals:
        if not merged or merged[-1][1] < interval[0]:
            merged.append(interval)
        else:
            merged[-1][1] = max(merged[-1][1], interval[1])

    return merged


def get_video_info(file_path):
    probe = ffmpeg.probe(file_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

    if not video_stream:
        raise ValueError("No video stream found")

    width = int(video_stream['width'])
    height = int(video_stream['height'])

    sar = video_stream.get('sample_aspect_ratio', '1:1')
    sar_width, sar_height = map(int, sar.split(':'))

    dar = video_stream.get('display_aspect_ratio', f"{width * sar_width}:{height * sar_height}")
    dar_width, dar_height = map(int, dar.split(':'))

    return width, height, sar_width, sar_height, dar_width, dar_height


def get_output_path_info_list(input_path_info_list):
    video_path_dict = {}

    output_path_info_list = []
    for path_info in input_path_info_list:
        story_path = path_info['story_path']
        if Path(story_path).name != 'story.json':
            continue

        with open(story_path) as f:
            story_data = json.load(f)

        output_section_info_list = story_data['output_section_info_list']

        video_dir = path_info['video_dir']

        for section_info in output_section_info_list:
            raw_caption_path = section_info['raw_caption_path']
            video_name = raw_caption_path.split("/")[-2]
            curr_video_dir = os.path.join(video_dir, video_name)

            if curr_video_dir not in video_path_dict:
                video_path_list = get_video_path_list(curr_video_dir)
                video_stem_dict = {Path(x).stem: x for x in video_path_list}
                video_path_dict[curr_video_dir] = video_stem_dict

            video_stem = Path(raw_caption_path).stem
            video_path = video_path_dict[curr_video_dir][video_stem]

            section_info['video_path'] = video_path

            if 'embedding' in section_info:
                del section_info['embedding']

        story_dir = str(Path(story_path).parent)
        story_dir = ensure_absolute_path(story_dir)

        output_video_path = f'{story_dir}/output_video.mp4'

        path_info['output_video_path'] = output_video_path
        path_info['output_section_info_list'] = output_section_info_list
        path_info['story_data'] = story_data

        output_path_info_list.append(path_info)

    return output_path_info_list


def handle_tmp_clip(video_dir, tmp_video_path_list, clip_list, output_fps, output_width, output_height, bg_color=(0, 0, 0)):
    tmp_video_path = f"{video_dir}/tmp_video_{len(tmp_video_path_list)}.mp4"
    temp_audio_path = f"{video_dir}/tmp_video_TEMP_MPY_wvf_snd.mp3"

    output_aspect_ratio = output_width / output_height

    adjusted_clips = []
    for clip in clip_list:
        w, h = clip.size
        clip_aspect_ratio = w / h

        if clip_aspect_ratio == output_aspect_ratio:
            adjusted_clip = clip.resize(newsize=(output_width, output_height))
        else:
            if clip_aspect_ratio > output_aspect_ratio:
                new_width = output_width
                new_height = int(output_width / clip_aspect_ratio)
            else:
                new_width = int(output_height * clip_aspect_ratio)
                new_height = output_height

            resized_clip = clip.resize(newsize=(new_width, new_height))
            adjusted_clip = resized_clip.on_color(size=(output_width, output_height), color=bg_color, pos='center')

        adjusted_clips.append(adjusted_clip)

    tmp_clip = concatenate_videoclips(adjusted_clips, method="compose")
    tmp_clip.write_videofile(tmp_video_path, codec="libx264", fps=output_fps, temp_audiofile=temp_audio_path)
    tmp_clip.close()
    tmp_video_path_list.append(tmp_video_path)

    for c in clip_list:
        c.close()

    clip_list.clear()


def output_tmp_video_txt(tmp_video_path_list, tmp_video_txt):
    with open(tmp_video_txt, 'w') as file:
        for video_path in tmp_video_path_list:
            file.write(f"file '{video_path}'\n")


def ensure_absolute_path(path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.abspath(path)


def merge_videos(tmp_video_txt, output_video_path, width, height):
    if (width is None) or (height is None):
        command = f"ffmpeg -y -f concat -safe 0 -i '{tmp_video_txt}' -c copy '{output_video_path}'"
    else:
        command = (
            f"ffmpeg -y -f concat -safe 0 -i '{tmp_video_txt}' "
            f"-vf 'scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2' "
            f"-c:v libx264 -preset fast -crf 22 '{output_video_path}'"
        )

    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error combining video: {e}")


def cleanup_files(tmp_video_txt, tmp_video_path_list):
    os.remove(tmp_video_txt)

    for video_path in tmp_video_path_list:
        os.remove(video_path)


def add_num_to_clip(clip, text, fontsize=100, color='red', font='Arial', margin_x=20, margin_y=20):
    txt_clip = TextClip(text,
                        fontsize=fontsize,
                        color=color,
                        font="./font/wqy-microhei.ttc",)

    txt_clip = txt_clip.set_duration(clip.duration).set_position((margin_x, margin_y)).set_start(0)
    return CompositeVideoClip([clip, txt_clip])


def add_text_to_clip(clip, text, fontsize=50, color='white', font='Arial'):
    txt_clip = TextClip(text,
                        fontsize=fontsize,
                        color=color,
                        font="./font/wqy-microhei.ttc",)
    txt_clip = txt_clip.set_duration(clip.duration).set_position('center').set_start(0)
    return CompositeVideoClip([clip, txt_clip])


def handle_one_path_info(path_info):
    batch_size = 10
    output_fps = 30

    output_width = 1280
    output_height = 720

    output_text = False

    if 'output_num' in path_info:
        output_num = path_info['output_num']
    else:
        output_num = False

    if 'use_real_id' in path_info:
        use_real_id = path_info['use_real_id']
    else:
        use_real_id = False

    print(f"\n{YELLOW}* output number: {output_num}{UNSET}")

    output_video_path = path_info['output_video_path']
    print(f"{PURPLE}process {output_video_path}{UNSET}")
    video_dir = str(Path(output_video_path).parent)
    output_section_info_list = path_info['output_section_info_list']
    story_data = path_info['story_data']
    story_result = story_data['story_result']
    if 'story' in story_result:
        story_caption_list = story_result['story']
    else:
        story_caption_list = story_result['clip_caption']

    section_id_list = story_result['section_id_list']

    time_intervals = [[section_info["start_time"], section_info["end_time"]]
                      for section_info in output_section_info_list]
    time_intervals = merge_intervals(time_intervals)
    print_duration(sum(end - start for start, end in time_intervals))

    clip_list = []
    tmp_video_path_list = []
    time_record_list = []
    total_duration = 0
    for i, (section_info, story_caption, real_clip_id) in enumerate(zip(output_section_info_list, story_caption_list, section_id_list)):
        start_time, end_time = section_info['start_time'], section_info['end_time']
        video_path = section_info['video_path']

        video_clip = VideoFileClip(video_path)
        if video_clip.rotation in (90, 270):
            video_clip = video_clip.resize(video_clip.size[::-1])
            video_clip.rotation = 0

        width, height, sar_width, sar_height, dar_width, dar_height = get_video_info(video_path)

        actual_width = width * sar_width // sar_height
        actual_height = height

        if actual_width / actual_height != width / height:
            video_clip = video_clip.resize(newsize=(actual_width, actual_height))

        if end_time > video_clip.duration:
            end_time = video_clip.duration

        clip = video_clip.subclip(start_time, end_time)

        if output_num:
            clip = add_num_to_clip(clip, f'{i}')
            if use_real_id:
                clip = add_num_to_clip(clip, str(real_clip_id), margin_x=20, margin_y=120)

        if output_text:
            clip = add_text_to_clip(clip, story_caption)

        clip_list.append(clip)

        if len(clip_list) == batch_size:
            handle_tmp_clip(video_dir, tmp_video_path_list, clip_list, output_fps, output_width, output_height)

        curr_duration = end_time - start_time

        record_start_time = total_duration
        record_end_time = total_duration + curr_duration

        total_duration = record_end_time

        time_record_list.append([record_start_time, record_end_time])

    if len(clip_list) > 0:
        handle_tmp_clip(video_dir, tmp_video_path_list, clip_list, output_fps, output_width, output_height)

    tmp_video_txt = f'{video_dir}/tmp_path_list.txt'
    output_tmp_video_txt(tmp_video_path_list, tmp_video_txt)

    merge_videos(tmp_video_txt, output_video_path, output_width, output_height)

    cleanup_files(tmp_video_txt, tmp_video_path_list)

    time_record_path = f'{video_dir}/time_record.json'
    with open(time_record_path, 'w') as f:
        json.dump(time_record_list, f, indent=2)

    print(f"{GREEN}done {output_video_path}{UNSET}\n")


def main(args):
    config_path = args.config_path
    config = yaml.load(open(config_path), Loader=yaml.FullLoader)

    read_data_config = [
        dict(
            dir_name='story_dir',
            type='json',
            path_name='story_path',
        )
    ]

    path_info_list = get_path_info_list(config, read_data_config)
    print(f'len(path_info_list): {len(path_info_list)}')

    output_path_info_list = get_output_path_info_list(path_info_list)

    for path_info in tqdm(output_path_info_list, ncols=80):
        handle_one_path_info(path_info)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str)
    args = parser.parse_args()
    main(args)
