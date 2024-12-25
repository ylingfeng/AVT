import argparse
import json
import os
import re
import sys

sys.path.pop(0)
sys.path.insert(0, '.')

import yaml
from tqdm import tqdm

from llms.gpt import gptv_caption
from utils.image import short_side_resize
from utils.misc import get_path_info_list
from utils.video import read_frames


def get_section_list(section_path):
    with open(section_path) as f:
        section_data = json.load(f)

    selected_section_list = section_data['selected_section_list']
    duplicated_section_list = section_data['duplicated_section_list']

    section_list = selected_section_list + duplicated_section_list
    section_list.sort(key=lambda x: x['start'])

    return section_list


def handle_one_path_info(path_info):

    video_path = path_info['video_path']
    section_path = path_info['section_path']
    raw_caption_path = path_info['raw_caption_path']

    config_path = path_info['config_path']
    tool_config = yaml.load(open(config_path), Loader=yaml.FullLoader)

    sample_rate = tool_config['sample_rate']
    short_side = tool_config['short_side']
    model = tool_config['model']

    section_list = get_section_list(section_path)

    section_caption_info_list = []

    video_info = None

    for section in tqdm(section_list, ncols=80):
        frame_list, sample_id_list, video_info = read_frames(video_path, section, sample_rate)

        frame_list = [short_side_resize(x, short_side)[0] for x in frame_list]
        fps = video_info['fps']

        start = section['start']
        end = section['end']

        start_time = round(start / fps, 1)
        end_time = round(end / fps, 1)

        for i in range(5):
            try:
                if 'gpt' in model:
                    response_str = gptv_caption(frame_list, tool_config)

                if response_str == tool_config['empty_caption']:
                    print(f'empty caption, video_path: {video_path}, section: [{start_time}, {end_time}]')

                response_str = response_str.strip()
                response_str = re.sub(r'(?<!")([a-zA-Z0-9_]+)(?!"):', r'"\1":', response_str)
                response_str = response_str.replace("```json", "").replace("```", "")
                attribute_all = json.loads(response_str)

                section_caption_info = dict(
                    start=section['start'],
                    end=section['end'],
                    start_time=start_time,
                    end_time=end_time,

                    raw_caption=str(attribute_all['raw_caption']),
                    attribute_caption_useful=str(attribute_all['attribute_useful']),
                    attribute_caption_useless=str(attribute_all['attribute_useless']),

                    sample_id_list=sample_id_list,
                    raw_section=section,
                )
                break

            except Exception as e:
                print(f'Try {i + 1}: Exception at gpt_get_attribute: "{e}".')
                print(response_str)
                section_caption_info = dict(
                    start=section['start'],
                    end=section['end'],
                    start_time=start_time,
                    end_time=end_time,

                    raw_caption=tool_config['empty_caption'],
                    attribute_caption_useful=tool_config['empty_caption'],
                    attribute_caption_useless=tool_config['empty_caption'],

                    sample_id_list=sample_id_list,
                    raw_section=section,
                )

        section_caption_info_list.append(section_caption_info)

    raw_caption_info = dict(
        section_caption_info_list=section_caption_info_list,
        video_info=video_info,
    )

    with open(raw_caption_path, 'w') as f:
        json.dump(raw_caption_info, f, indent=2)


def main(args):
    config_path = args.config_path
    config = yaml.load(open(config_path, encoding='UTF-8'), Loader=yaml.FullLoader)

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
        ),
        dict(
            dir_name='raw_caption_dir',
            type='json',
            path_name='raw_caption_path',
            is_output=True,
        )
    ]

    path_info_list = get_path_info_list(config, read_data_config)
    print(f'len(path_info_list): {len(path_info_list)}')

    for path_info in tqdm(path_info_list, ncols=80):
        print(f"\nprocess {path_info['video_path']}")
        handle_one_path_info(path_info)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str)
    args = parser.parse_args()
    main(args)
