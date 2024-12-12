import argparse
import json
import os
import sys

sys.path.pop(0)
sys.path.insert(0, '.')

import cv2
import yaml
from dotenv import load_dotenv
from joblib import Parallel, delayed

from utils.misc import get_path_info_list

load_dotenv()


def handle_one_path_info(path_info):

    video_path = path_info['video_path']
    section_path = path_info['section_path']

    section_size = path_info['section_size']
    section_stride = path_info['section_stride']

    video_capture = cv2.VideoCapture(video_path)
    if not video_capture.isOpened():
        print(f'read video {video_path} fail')
        return

    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video_capture.get(cv2.CAP_PROP_FPS)

    size_len = int(round(section_size * fps))
    size_len = max(size_len, 2)

    stride_len = int(round(section_stride * fps))
    stride_len = max(stride_len, 2)

    all_section_list = []
    selected_section_list = []
    for start in range(0, frame_count, stride_len):
        end = start + size_len
        end = min(end, frame_count)

        section_item = dict(
            start=start,
            end=end,
        )

        all_section_list.append(section_item)
        if end == (start + size_len):
            selected_section_list.append(section_item)

        if end >= frame_count:
            break

    output_section_data = dict(
        all_section_list=all_section_list,
        selected_section_list=selected_section_list,
        duplicated_section_list=[],
    )

    with open(section_path, 'w') as f:
        json.dump(output_section_data, f, indent=2)


def main(args):
    config_path = args.config_path
    config = yaml.load(open(config_path), Loader=yaml.FullLoader)

    read_data_config = [
        dict(
            dir_name='video_dir',
            type='video',
            path_name='video_path',
        ),
        dict(
            dir_name='section_dir',
            type='json',
            path_name='section_path',
            is_output=True,
        ),
    ]

    path_info_list = get_path_info_list(config, read_data_config)
    print(f'len(path_info_list): {len(path_info_list)}')

    n_jobs = config['n_jobs']
    Parallel(n_jobs=n_jobs, verbose=10)(
        delayed(handle_one_path_info)(x) for x in path_info_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str)
    args = parser.parse_args()
    main(args)
