import json
import re


def parse_story(message):
    story = []
    section_id_list = []
    # story = re.findall(r"STORY(.*?)", message)[0]
    # print(story)
    sentences = re.findall(r'\[(.*?)\]', message)
    for s in sentences:
        clip_id = re.findall(r"[\<]*.*?(\d+).*?[\>]*", s)[0]

        story.append(s)
        section_id_list.append(clip_id)

    assert len(section_id_list) >= 1, "list is empty"
    section_info = dict(
        story=story,
        section_id_list=[int(x.strip()) for x in section_id_list],
    )
    return section_info


def parse_story_v2(message):
    story = []
    section_id_list = []
    sentences = re.findall(r'\[(.*?)\]', message)
    found_clip_id = False

    for s in sentences:
        clip_ids = re.findall(r"[\<]*.*?(\d+).*?[\>]*", s)
        if clip_ids:
            clip_id = clip_ids[0]
            story.append(s)
            section_id_list.append(clip_id)
            found_clip_id = True

    if not found_clip_id:
        return None

    assert len(section_id_list) >= 1
    section_info = dict(
        story=story,
        section_id_list=[int(x.strip()) for x in section_id_list],
    )
    return section_info


def parse_story_v3(response_str):
    section_info = json.loads(response_str)

    return section_info
