from .get_video import *


def simple_output_video(video_dir, output_video_path, all_info_list, id_list):
    print(output_video_path)
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

    video_path_dict = {}

    output_section_info_list = [all_info_list[i] for i in id_list]
    story_caption_list = [x["raw_caption"] for x in output_section_info_list]
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

    batch_size = 10
    output_fps = 30

    output_width = 1280
    output_height = 720

    output_text = False

    output_num = False

    clip_list = []
    tmp_video_path_list = []
    video_dir = str(Path(output_video_path).parent)

    time_record_list = []
    total_duration = 0

    for i, (section_info, story_caption) in enumerate(zip(output_section_info_list, story_caption_list)):
        start_time, end_time = section_info['start_time'], section_info['end_time']
        video_path = section_info['video_path']

        video_clip = VideoFileClip(video_path)
        if video_clip.rotation in (90, 270):
            video_clip = video_clip.resize(video_clip.size[::-1])
            video_clip.rotation = 0

        width, height, sar_width, sar_height, dar_width, dar_height = get_video_info(video_path)
        dar_ratio = dar_width / dar_height

        actual_width = width * sar_width // sar_height
        actual_height = height

        if actual_width / actual_height != width / height:
            video_clip = video_clip.resize(newsize=(actual_width, actual_height))

        if end_time > video_clip.duration:
            end_time = video_clip.duration

        clip = video_clip.subclip(start_time, end_time)

        if output_num:
            clip = add_num_to_clip(clip, f'{i}')

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
