import argparse
import copy
import json
import os
import sys
from pathlib import Path

sys.path.pop(0)
sys.path.insert(0, '.')

import yaml
from tqdm import tqdm

from utils.color_print import PINK, PURPLE, UNSET
from utils.methods import *
from utils.misc import get_path_info_list


def string_to_json(input_str):
    if input_str == 'EMPTY':
        return {
            "Highlight": 0,
            "Defect": 0,
        }
    data = {}

    pairs = input_str.split(';')

    for pair in pairs:
        if pair.strip():
            key, value = pair.split(':')
            key = key.strip().strip('[]')
            value = float(value.strip())
            data[key] = value
    return data


def process_string(s):
    attribute = string_to_json(s)

    margin = -0.2
    neg_score = max(max([attribute[k] for k in attribute.keys() if k not in ["Highlight"]]) + margin, 0)
    pos_score = attribute["Highlight"]

    if neg_score > pos_score:
        raw_score = pos_score - neg_score
    else:
        raw_score = pos_score

    if raw_score >= 0.6:
        return False, True, raw_score
    elif raw_score < 0:
        return True, False, raw_score
    else:
        return False, False, raw_score
    # useless_flag, highlight_flag, score


def get_filter(path_info_list):
    available_section_info_list = []
    available_section_id_list = []
    all_section_info_list = []
    all_section_id_list = []
    all_clip_num = 0

    for path_info in path_info_list:
        raw_caption_path = path_info['raw_caption_path']
        caption_path = path_info['caption_path']

        with open(raw_caption_path) as f:
            caption_data = json.load(f)

        section_caption_info_list = caption_data['section_caption_info_list']

        for section_caption_info in section_caption_info_list:
            output_section_info = copy.deepcopy(section_caption_info)
            output_section_info['raw_caption_path'] = raw_caption_path

            # filter out the waste section
            useless_flag, highlight_flag, score = process_string(section_caption_info['attribute_caption_useless'])
            if highlight_flag:
                output_section_info['Highlight'] = f"['Highlight Score']: {score}"
            else:
                output_section_info['Highlight'] = "['Highlight Score']: 0"

            output_section_info["clip_id"] = all_clip_num
            if useless_flag is not True:
                available_section_info_list.append(output_section_info)
                available_section_id_list.append(all_clip_num)
            all_section_info_list.append(output_section_info)
            all_section_id_list.append(all_clip_num)
            all_clip_num = all_clip_num + 1

        with open(caption_path, 'w') as f:
            json.dump(available_section_info_list, f, indent=2)

    return available_section_id_list, all_section_id_list, all_section_info_list, all_clip_num


def handle_one_dir_info(dir_info):
    print(f"\n{PURPLE}process {dir_info['output_path']}{UNSET}")

    ################################ load configs ###############################
    path_info_list = dir_info['path_info_list']
    path_info = path_info_list[0]
    output_path = dir_info['output_path']
    for k, v in path_info.items():
        if "config_path" in k:
            print(f"* {k}: {v}")

    config_path_step1 = path_info['config_path_step1']
    tool_config = yaml.load(open(config_path_step1), Loader=yaml.FullLoader)

    config_path_step2 = path_info['config_path_step2']
    tool_config_step2 = yaml.load(open(config_path_step2), Loader=yaml.FullLoader)

    config_path_step3 = path_info['config_path_step3']
    tool_config_step3 = yaml.load(open(config_path_step3), Loader=yaml.FullLoader)

    ################################### filter ##################################
    available_section_id_list, all_section_id_list, all_section_info_list, all_clip_num = get_filter(path_info_list)

    print(f"* filter: selected {len(available_section_id_list)} out of {len(all_section_info_list)}: "
          f"{available_section_id_list}")

    save_dir = os.path.join(os.path.dirname(output_path), "available_section_id_list.json")
    with open(save_dir, 'w') as f:
        json.dump(available_section_id_list, f, ensure_ascii=False)

    save_dir = os.path.join(os.path.dirname(output_path), "all_section_info_list.json")
    with open(save_dir, 'w') as f:
        json.dump(all_section_info_list, f, indent=2, ensure_ascii=False)

    if "skip_story" in path_info and path_info['skip_story']:
        return

    ################################# get story #################################
    STEP1_THR = 15
    if len(available_section_id_list) < STEP1_THR:
        id_list = all_section_id_list
    else:
        id_list = available_section_id_list
    # print(f"{PINK}==>{UNSET} clips used for story: {len(id_list)}, {id_list}")

    ############################## step1 get story ##############################
    use_step1 = len(id_list) > tool_config['min_CLIP']
    multi_step1 = False
    list_length = len(id_list)

    if use_step1:
        if list_length >= 30:
            max_CLIP = min(list_length // 3 + 1, 15)

            id_list_step1, story_step1 = get_story_step1(tool_config, all_section_info_list, id_list, max_CLIP)
        else:
            id_list_step1 = id_list
            story_step1 = dict(
                story=[f'{i}: {all_section_info_list[i]["raw_caption"]}' for i in id_list_step1],
                section_id_list=id_list_step1,
            )
        print(f"* step1 story: selected {len(id_list_step1)} out of {list_length}: {id_list_step1}")

        ############################ after step1 get story ###########################
        loop = 0
        while len(id_list_step1) > 50:
            loop += 1
            multi_step1 = True
            tmp_length = len(id_list_step1)
            print(f"{PINK}==>{UNSET} after step1 story (extra step{loop})")
            max_CLIP = min(len(id_list_step1) // 10 + 1, 15)
            id_list_step1, story_step1 = get_story_step1(tool_config, all_section_info_list, id_list_step1, max_CLIP,
                                                         skip_None=True, NAME=f"after step1 story (extra step{loop})")
            print(
                f"* after step1 story (extra step{loop}): selected {len(id_list_step1)} out of {tmp_length}: {id_list_step1}")
            if loop == 3:
                break

        if len(id_list_step1) == 0:
            print("* empty selected after step1, use all useful")
            id_list_step1 = id_list
            story_step1 = dict(
                story=[f'{i}: {all_section_info_list[i]["raw_caption"]}' for i in id_list_step1],
                section_id_list=id_list_step1,
            )
    else:
        print("* skip step1")
        id_list_step1 = id_list
        story_step1 = dict(
            story=[f'{i}: {all_section_info_list[i]["raw_caption"]}' for i in id_list_step1],
            section_id_list=id_list_step1,
        )
        print(f"* step1 story: selected {len(id_list_step1)} out of {list_length}: {id_list_step1}")

    ############################## step2 get story ##############################
    if id_list_step1:
        lb = 20
        ub = 40
        id_list_step2, story_step2 = get_story_step2(tool_config_step2, all_section_info_list, id_list_step1,
                                                     skip_None=True, lb=lb, ub=ub)
    else:
        id_list_step2 = []
        story_step2 = None

    print(f"* step2 story: selected {len(id_list_step2)} out of {len(id_list_step1)}: {id_list_step2}")

    ######################## step2 merge or concat story ########################
    multi_step2 = False
    skip_step2 = len(id_list_step2) < lb and len(id_list_step1) >= ub

    if len(id_list_step2) > 30 or skip_step2:
        multi_step2 = True
        print("* after step2 story (extra step1)")
        if skip_step2:
            id_list_step2 = id_list_step1
            print("* step2 story reduce too much segments, replace step2 with another step1.")
        max_CLIP = min(len(id_list_step2) // 5, 15)
        tmp_length = len(id_list_step2)
        id_list_step2, story_step2 = get_story_step1(tool_config, all_section_info_list, id_list_step2, max_CLIP,
                                                     skip_None=True, NAME="after step2 story (extra step1)")
        print(f"* after step2 story (extra step1): selected {len(id_list_step2)} out of {tmp_length}: "
              f"{id_list_step2}")

        choose_clip_info = (f"step2 story: use multi step2, skip step2 ({skip_step2}). multi step1 ({multi_step1}), multi step2 ({multi_step2}), "
                            f"story choose: {len(id_list_step2)}, all story video clip: {len(id_list_step1)}, "
                            f"all useful video clip: {len(id_list)}, all video clip: {all_clip_num}")
        id_list_out = id_list_step2

    elif len(id_list_step2) >= 15:
        choose_clip_info = (f"step2 story: use merge. multi step1 ({multi_step1}), multi step2 ({multi_step2}), "
                            f"story choose: {len(id_list_step2)}, all story video clip: {len(id_list_step1)}, "
                            f"all useful video clip: {len(id_list)}, all video clip: {all_clip_num}")
        id_list_out = id_list_step2

    elif len(id_list_step2) < 15 and list_length < 30:
        choose_clip_info = (f"step2 story: use all. multi step1 ({multi_step1}), multi step2 ({multi_step2}), "
                            f"story choose (skip): {len(id_list_step1)} , all story video clip (skip): {len(id_list_step1)}, "
                            f"all useful video clip: {len(id_list)}, all video clip: {all_clip_num}")
        id_list_out = id_list_step1

    else:
        choose_clip_info = (f"step2 story: use all. multi step1 ({multi_step1}), multi step2 ({multi_step2}), "
                            f"story choose: {len(id_list_step1)}, all story video clip: {len(id_list_step1)}, "
                            f"all useful video clip: {len(id_list)}, all video clip: {all_clip_num}")
        id_list_out = id_list_step1

    print(f"{PINK}==>{UNSET} {choose_clip_info}")
    print(f"{PINK}==>{UNSET} step3 story: inputs {len(id_list_out)}: {id_list_out}")
    id_list_step3, story_step3 = get_story_step3(tool_config_step3, all_section_info_list, id_list_out,
                                                 NAME="step3 story")
    print(f"{PINK}==>{UNSET} step3 story: outputs {len(id_list_step3)}: {id_list_step3}")
    output_story_data = dict(
        choose_clip_info=choose_clip_info,
        story_result=story_step3,
        output_section_info_list=[all_section_info_list[i] for i in id_list_step3],
    )
    ################################ save stories ###############################
    with open(output_path, 'w') as f:
        json.dump(output_story_data, f, indent=2, ensure_ascii=False)

    return


def get_dir_info_list(path_info_list):

    path_info_dict = {}

    for path_info in path_info_list:
        raw_caption_path = path_info['raw_caption_path']

        dir_name = str(Path(raw_caption_path).parent)
        if dir_name not in path_info_dict:
            path_info_dict[dir_name] = []

        path_info_dict[dir_name].append(path_info)

    dir_info_list = []
    for dir_name, curr_path_info_list in path_info_dict.items():
        tmp_output_path = curr_path_info_list[0]['story_path']
        tmp_output_dir = str(Path(tmp_output_path).parent)
        output_path = f'{tmp_output_dir}/story.json'

        dir_info = dict(
            dir_name=dir_name,
            path_info_list=curr_path_info_list,
            output_path=output_path,
        )

        dir_info_list.append(dir_info)

    dir_info_list.sort(key=lambda x: x['dir_name'])
    return dir_info_list


def main(args):
    config_path = args.config_path
    config = yaml.load(open(config_path, encoding='UTF-8'), Loader=yaml.FullLoader)

    read_data_config = [
        dict(
            dir_name='raw_caption_dir',
            type='json',
            path_name='raw_caption_path',
        ),
        dict(
            dir_name='story_dir',
            type='json',
            path_name='story_path',
            is_output=True,
        ),
        dict(
            dir_name='caption_dir',
            type='json',
            path_name='caption_path',
            is_output=True,
        )
    ]

    path_info_list = get_path_info_list(config, read_data_config)
    print(f'len(path_info_list): {len(path_info_list)}')

    dir_info_list = get_dir_info_list(path_info_list)

    for dir_info in tqdm(dir_info_list, ncols=80):
        handle_one_dir_info(dir_info)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path', type=str)
    args = parser.parse_args()
    main(args)
