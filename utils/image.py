import base64

import cv2


def short_side_resize(image, short_side):
    h, w, _ = image.shape

    curr_short_side = min(h, w)
    resize_ratio = short_side / curr_short_side

    new_h = int(h * resize_ratio)
    new_w = int(w * resize_ratio)
    resized_image = cv2.resize(image, (new_w, new_h))
    return resized_image, resize_ratio


def long_side_resize(image, long_side):
    h, w, _ = image.shape

    curr_long_side = max(h, w)
    resize_ratio = long_side / curr_long_side

    new_h = int(h * resize_ratio)
    new_w = int(w * resize_ratio)
    resized_image = cv2.resize(image, (new_w, new_h))
    return resized_image, resize_ratio


def center_crop(image, ratio):
    assert (ratio < 1) and (ratio > 0), f'invalid ratio: {ratio:.2f}'

    h, w, _ = image.shape

    new_h = int(round(h * ratio))
    new_h = max(new_h, 1)

    h_start = (h - new_h) // 2
    h_end = h_start + new_h

    new_w = int(round(w * ratio))
    new_w = max(new_w, 1)

    w_start = (w - new_w) // 2
    w_end = w_start + new_w

    cropped_image = image[h_start: h_end, w_start: w_end, :]

    return cropped_image


def encode_cv2_image(image):
    _, buffer = cv2.imencode('.jpg', image)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    return image_base64
