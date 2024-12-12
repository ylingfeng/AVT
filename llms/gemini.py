import io

import cv2
import google.generativeai as genai
from PIL import Image

from utils.image import encode_cv2_image


def encode_cv2_image_to_PIL(image):
    _, buffer = cv2.imencode('.jpg', image)
    pil_image = Image.open(io.BytesIO(buffer))

    return pil_image


def gemini_caption(frame_list, tool_config):

    genai.configure(api_key="GEMINI_API_KEY")

    client = genai.GenerativeModel('gemini-1.5-flash')

    invalid_keyword_list = ["sorry", "cannot assist", "cannot provide", "can't assist"]

    encoded_frame_list = [encode_cv2_image_to_PIL(x) for x in frame_list]

    max_try_count = tool_config['max_try_count']
    for i in range(max_try_count):
        try:
            prompt = tool_config['prompt']['system'] + '\n\n' + tool_config['prompt']['user']
            result = client.generate_content([prompt] + encoded_frame_list)
            message = result.text
            if not any([s in message.lower() for s in invalid_keyword_list]):
                return message

        except Exception as e:
            print(f"Exception at gemini_caption: {e}")

    empty_caption = tool_config['empty_caption']
    return empty_caption
