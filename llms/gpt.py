from openai import OpenAI

from utils.color_print import UNSET, YELLOW
from utils.image import encode_cv2_image

GPT_API_KEY = None
BASE_URL = None


def gptv_caption(frame_list, tool_config):
    invalid_keyword_list = ["sorry", "cannot assist", "cannot provide", "can't assist"]

    client = OpenAI(api_key=GPT_API_KEY, base_url=BASE_URL)
    temperature = tool_config['temperature'] if 'temperature' in tool_config else 0.5

    short_side = tool_config['short_side']

    encoded_frame_list = [encode_cv2_image(x) for x in frame_list]

    max_try_count = tool_config['max_try_count']
    for i in range(max_try_count):
        try:
            result = client.chat.completions.create(
                model=tool_config['model'],
                messages=[
                    {"role": "system", "content": tool_config['prompt']['system']},
                    {
                        "role": "user",
                        "content": [
                            tool_config['prompt']['user'],
                            *map(lambda x: {"image": x, "resize": short_side},
                                 encoded_frame_list),
                        ],
                    },
                ],
                max_tokens=tool_config['max_tokens'],
                temperature=temperature
            )

            message = result.choices[0].message.content
            if not any([s in message.lower() for s in invalid_keyword_list]):
                return message

        except Exception as e:
            print(f"{YELLOW}Exception at gptv_caption: {e}{UNSET}")

    empty_caption = tool_config['empty_caption']
    return empty_caption


def gpt_refine_caption(raw_caption, tool_config):
    invalid_keyword_list = ["sorry", "cannot assist", "cannot provide", "can't assist"]

    client = OpenAI(api_key=GPT_API_KEY, base_url=BASE_URL)
    temperature = tool_config['temperature'] if 'temperature' in tool_config else 0.5

    max_try_count = tool_config['max_try_count']
    for i in range(max_try_count):
        try:
            result = client.chat.completions.create(
                model=tool_config['model'],
                messages=[
                    {"role": "system", "content": tool_config['prompt']['system']},
                    {"role": "user", "content": tool_config['prompt']['user']},
                    {"role": "user", "content": raw_caption},
                ],
                temperature=temperature
            )

            message = result.choices[0].message.content
            if not any([s in message.lower() for s in invalid_keyword_list]):
                return message

        except Exception as e:
            print(f"{YELLOW}Exception at gpt_refine_caption: {e}{UNSET}")

    empty_caption = tool_config['empty_caption']
    return empty_caption


def gpt_get_embedding(text, tool_config):
    text = text.replace("\n", " ")

    client = OpenAI(api_key=GPT_API_KEY, base_url=BASE_URL)

    max_try_count = tool_config['max_try_count']
    model = tool_config['model']

    assert model == 'text-embedding-3-small', f'tool_config: {tool_config}'

    default_embedding = [0 for _ in range(1536)]

    for i in range(max_try_count):
        try:
            embedding = client.embeddings.create(input=[text], model=model).data[0].embedding
            return embedding

        except Exception as e:
            print(f"{YELLOW}Exception at gpt_get_embedding: {e}{UNSET}")

    print(f'get embedding fail, return default embedding')
    return default_embedding


def gpt_remove_waste_section(text, tool_config):
    invalid_keyword_list = ["sorry", "cannot assist", "cannot provide", "can't assist"]

    client = OpenAI(api_key=GPT_API_KEY, base_url=BASE_URL)
    temperature = tool_config['temperature'] if 'temperature' in tool_config else 0.5

    max_try_count = tool_config['max_try_count']
    for i in range(max_try_count):
        try:
            result = client.chat.completions.create(
                model=tool_config['model'],
                messages=[
                    {"role": "system", "content": tool_config['prompt']['system']},
                ],
                temperature=temperature
            )

            message = result.choices[0].message.content
            if not any([s in message.lower() for s in invalid_keyword_list]):
                # print(f'gpt_caption try count: {i + 1}')
                return message

        except Exception as e:
            print(f"{YELLOW}Exception at gpt_refine_caption: {e}{UNSET}")

    empty_caption = tool_config['empty_caption']
    return empty_caption


def gpt_get_story(caption_text, tool_config, name="gpt_get_story"):
    prompt = tool_config['prompt']['system']

    invalid_keyword_list = ["sorry", "cannot assist", "cannot provide", "can't assist"]

    client = OpenAI(api_key=GPT_API_KEY, base_url=BASE_URL)
    temperature = tool_config['temperature'] if 'temperature' in tool_config else 0.5

    max_try_count = tool_config['max_try_count']
    for i in range(max_try_count):
        try:
            result = client.chat.completions.create(
                model=tool_config['model'],
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": caption_text},
                ],
                temperature=temperature
            )

            message = result.choices[0].message.content
            if not any([s in message.lower() for s in invalid_keyword_list]):
                # print(f'gpt_caption try count: {i + 1}')
                return message

        except Exception as e:
            print(f"{YELLOW}Exception at {name}: {e}{UNSET}")

    empty_caption = tool_config['empty_caption']
    return empty_caption


def gpt_get_story_with_instruction(caption_text, tool_config, instruction, name="gpt_get_story_with_instruction"):
    prompt = tool_config['prompt']['system'].replace("[INS]", instruction)

    invalid_keyword_list = ["sorry", "cannot assist", "cannot provide", "can't assist"]

    client = OpenAI(api_key=GPT_API_KEY, base_url=BASE_URL)
    temperature = tool_config['temperature'] if 'temperature' in tool_config else 0.5

    max_try_count = tool_config['max_try_count']
    for i in range(max_try_count):
        try:
            result = client.chat.completions.create(
                model=tool_config['model'],
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": caption_text},
                ],
                temperature=temperature
            )

            message = result.choices[0].message.content
            if not any([s in message.lower() for s in invalid_keyword_list]):
                # print(f'gpt_caption try count: {i + 1}')
                return message

        except Exception as e:
            print(f"{YELLOW}Exception at {name}: {e}{UNSET}")

    empty_caption = tool_config['empty_caption']
    return empty_caption
