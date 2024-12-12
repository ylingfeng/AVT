import json
import os
import sys

sys.path.pop(0)
sys.path.insert(0, '.')

import numpy as np

from llms.gpt import gpt_get_story
from utils.color_print import PINK, UNSET, YELLOW
from utils.parse import parse_story, parse_story_v2, parse_story_v3
from utils.util import unique_elements_with_indices


def format_captions(caption_info_list, keys=["clip_id", "Highlight", "raw_caption", "attribute_caption_useful"], id_list=None):
    captions_list = []

    for id, x in enumerate(caption_info_list):
        cap = []
        for k in keys:
            if k == "clip_id":
                if id_list is None:
                    cap += [f'<{id}>']
                else:
                    cap += [f'<{id_list[id]}>']
            else:
                cap += [f'<{x[k]}>']
        cap = ", ".join(cap)
        captions_list.append(cap)

    captions_str = "|".join(captions_list)
    return captions_str


def get_story_step1(cfg, all_info_list, id_list, max_CLIP, skip_None=False, NAME="step1 story"):
    parse = cfg["parse"]
    info_list = [all_info_list[i] for i in id_list]

    slices = [info_list[i:i + max_CLIP] for i in range(0, len(info_list), max_CLIP)]
    section_id_slices_matrix = np.zeros(len(info_list))
    max_try_count = cfg['max_try_count']

    story_text_all = []

    print(f"{PINK}==>{UNSET} {NAME}: num clips selected: {len(info_list)}, "
          f"num slices: {len(slices)}, slice len: {[len(x) for x in slices]}")
    for slice_id in range(len(slices)):
        caption_text = format_captions(slices[slice_id])
        for j in range(max_try_count):
            raw_story_result = gpt_get_story(caption_text, cfg, f"{NAME}: slice {slice_id + 1}")

            try:
                story_result = eval(parse)(raw_story_result)

                if skip_None and story_result is None:
                    print("* Not found highlight section, do next! ")
                    break

                story_text = story_result['story']
                section_id_list = story_result['section_id_list']

                if section_id_list is not None:
                    print(f"{PINK}==>{UNSET} {NAME}: slice {slice_id + 1}: "
                          f"{[id_list[(slice_id * max_CLIP) + k] for k in section_id_list]}")
                    for k in section_id_list:
                        section_id_slices_matrix[(slice_id * max_CLIP) + k] = 1
                    assert len(story_text) == len(section_id_list)

                    unique_id = np.unique(section_id_list)
                    if len(story_text) != len(unique_id):
                        pass
                    _, indices = unique_elements_with_indices(section_id_list)
                    story_text = [story_text[ind] for ind in indices]

                    story_text_all += story_text
                break

            except Exception as e:
                print(f"{YELLOW}Exception at parsing {NAME}: slice {slice_id + 1}: {e}{UNSET}")

    out_id_list = [id_list[i] for i, value in enumerate(section_id_slices_matrix) if value == 1]
    assert len(section_id_slices_matrix) == len(id_list)
    assert len(story_text_all) == len(out_id_list)

    story_text_all = [f"{i}: {s.split(': ', 1)[1]}" for i, s in zip(out_id_list, story_text_all)]
    story_result_all = dict(
        story=story_text_all,
        section_id_list=out_id_list,
    )

    return out_id_list, story_result_all


def get_story_step2(cfg, all_info_list, id_list, skip_None=False, NAME="step2 story", lb=20, ub=40):
    parse = cfg["parse"]
    info_list = [all_info_list[i] for i in id_list]

    caption_text = format_captions(info_list)
    max_try_count = 3

    for j in range(max_try_count):
        raw_story_result = gpt_get_story(caption_text, cfg, NAME)

        try:
            story_result = eval(parse)(raw_story_result)

            if skip_None and story_result is None:
                print("* get None story, try again! ")
                continue

            out_id_list = [id_list[i] for i in story_result['section_id_list']]
            story_result['section_id_list'] = out_id_list
            story_result["story"] = [f"{i}: {s.split(': ', 1)[1]}" for i, s in zip(out_id_list, story_result["story"])]

            if len(out_id_list) < lb and len(id_list) >= ub:
                print(f"{PINK}==>{UNSET} {NAME}: {j+1}, "
                      f"get story {len(out_id_list)} out of {len(id_list)}, reduce too much segments, try again.")
                if j + 1 == max_try_count:
                    print(f"{PINK}==>{UNSET} {NAME}: exceed max try count, output {len(out_id_list)}.")
                continue
            else:
                print(f"{PINK}==>{UNSET} {NAME}: {j+1}, "
                      f"get story {len(out_id_list)} out of {len(id_list)}, succeed.")
                break

        except Exception as e:
            print(f"{YELLOW}Exception at parsing {NAME}: {e}{UNSET}")
            if j + 1 == max_try_count:
                out_id_list = []
                story_result = None

    return out_id_list, story_result


def get_story_step3(cfg, all_info_list, id_list, NAME="step3 story"):
    parse = cfg["parse"]
    info_list = [all_info_list[i] for i in id_list]

    caption_text = format_captions(info_list)
    max_try_count = cfg['max_try_count']

    for j in range(max_try_count):
        raw_story_result = gpt_get_story(caption_text, cfg, NAME)

        try:
            result_dict = eval(parse)(raw_story_result)

            out_id_list = [id_list[int(i)] for i in result_dict['clip_caption']]
            assert out_id_list == id_list, "in != out"

            story_result = {}
            story_result['section_id_list'] = out_id_list
            story_result["clip_caption"] = {id_list[int(k)]: v for k, v in result_dict["clip_caption"].items()}
            story_result["theme_caption"] = {str([id_list[int(i)] for i in json.loads(k.replace("'", '"'))]): v
                                             for k, v in result_dict["theme_caption"].items()}
            story_result["global_caption"] = result_dict["global_caption"]

            break

        except Exception as e:
            print(f"{YELLOW}Exception at parsing {NAME}: {e}{UNSET}")
            print(f"{YELLOW}{raw_story_result}{UNSET}")
            if j + 1 == max_try_count:
                out_id_list = []
                story_result = None

    return out_id_list, story_result
