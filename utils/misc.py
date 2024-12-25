import copy
from pathlib import Path

import numpy as np


def video_suffix_list():
    video_suffix_list = ['.mp4', '.mov', '.webm', '.mkv', '.lrv']
    return video_suffix_list


def get_video_path_list(input_dir, recursive=False):
    # accepted_suffix = ['.mp4', '.mov', '.webm', '.mkv']
    # accepted_suffix = ['.mp4', '.mov', '.webm', '.mkv', '.lrv']
    accepted_suffix = video_suffix_list()

    lower_suffix_list = [x.lower() for x in accepted_suffix]
    upper_suffix_list = [x.upper() for x in accepted_suffix]
    suffix_list = lower_suffix_list + upper_suffix_list

    total_path_list = []
    for suffix in suffix_list:
        if recursive:
            path_list = list(Path(input_dir).rglob(f'*{suffix}'))
        else:
            path_list = list(Path(input_dir).glob(f'*{suffix}'))

        path_list = list(filter(lambda x: x.is_file() and (not x.stem.startswith('._')), path_list))
        path_list = [str(x) for x in path_list]
        total_path_list += path_list

    return np.unique(total_path_list).tolist()


def get_config_item(data_item, tmp_path_info, name, default_value=None):
    if name in data_item:
        config_item = data_item[name]

    elif name in tmp_path_info:
        config_item = tmp_path_info[name]
    else:
        config_item = default_value

    return config_item


def handle_one_group_name(read_data_config, tmp_path_info, data_item, group_name):
    curr_path_info_list = []

    first_read_config = read_data_config[0]
    first_dir_name = first_read_config['dir_name']
    first_dir = data_item[first_dir_name]
    first_type = first_read_config['type']
    first_path_name = first_read_config['path_name']

    first_is_output = False
    if 'is_output' in first_read_config:
        first_is_output = first_read_config['is_output']

    assert not first_is_output, f'read_data_config: {read_data_config}'

    if group_name is not None:
        first_dir = f'{first_dir}/{group_name}'

    if first_type == 'video':
        first_item_path_list = get_video_path_list(first_dir)
    else:
        first_item_path_list = [str(x) for x in Path(first_dir).glob(f'*.{first_type}')]

    dir_name_list = [x['dir_name'] for x in read_data_config]

    for first_item_path in first_item_path_list:
        first_item_stem = Path(first_item_path).stem

        flag = False

        for read_data_config_item in read_data_config[1:]:
            curr_dir_name = read_data_config_item['dir_name']
            curr_type = read_data_config_item['type']
            curr_dir = data_item[curr_dir_name]

            curr_is_output = False
            if 'is_output' in read_data_config_item:
                curr_is_output = read_data_config_item['is_output']

            assert curr_type != 'video', f'type other than the first one cannot be "video"'

            if group_name is not None:
                curr_dir = f'{curr_dir}/{group_name}'

            curr_item_path = f'{curr_dir}/{first_item_stem}.{curr_type}'
            if (not curr_is_output) and (not Path(curr_item_path).is_file()):

                flag = True
                break

        if flag:
            continue

        curr_path_info = copy.deepcopy(tmp_path_info)
        assert first_path_name not in curr_path_info, f'{first_path_name} has already existed in curr_path_info'
        curr_path_info[first_path_name] = first_item_path

        for read_data_config_item in read_data_config[1:]:
            curr_dir_name = read_data_config_item['dir_name']
            curr_dir = data_item[curr_dir_name]
            curr_type = read_data_config_item['type']
            curr_path_name = read_data_config_item['path_name']

            if group_name is not None:
                curr_dir = f'{curr_dir}/{group_name}'

            if ('is_output' in read_data_config_item) and read_data_config_item['is_output']:
                Path(curr_dir).mkdir(exist_ok=True, parents=True)

            curr_item_path = f'{curr_dir}/{first_item_stem}.{curr_type}'
            curr_path_info[curr_path_name] = curr_item_path

        for key, value in data_item.items():
            if key not in dir_name_list:
                curr_path_info[key] = value

        curr_path_info_list.append(curr_path_info)

    return curr_path_info_list


def adjust_path_info_list(read_data_config, data_name, data_item, tmp_path_info,
                          curr_path_info_list, first_path_name, group_mode, selected_group_name_list):
    input_name = get_config_item(data_item, tmp_path_info, 'input_name', default_value=None)
    input_num = get_config_item(data_item, tmp_path_info, 'input_num', default_value=-1)

    raw_overwrite = get_config_item(data_item, tmp_path_info, 'overwrite', default_value=False)
    overwrite = raw_overwrite

    curr_path_info_list.sort(key=lambda x: x[first_path_name])
    total_num = len(curr_path_info_list)

    if not overwrite:
        exist_stem_list = []

        check_read_config = None
        for read_data_config_item in read_data_config:
            if ('is_output' in read_data_config_item) and read_data_config_item['is_output']:
                check_read_config = read_data_config_item

        # assert check_read_config is not None, f'read_data_config: {read_data_config}'
        if check_read_config is not None:
            check_dir_name = check_read_config['dir_name']
            check_dir = data_item[check_dir_name]

            check_type = check_read_config['type']
            assert check_type != 'video', f'type other than the first one cannot be "video"'

            if group_mode:
                group_name_list = [x.name for x in Path(check_dir).glob('*') if x.is_dir()]

                if len(selected_group_name_list) > 0:
                    group_name_list = [x for x in group_name_list if x in selected_group_name_list]

            else:
                group_name_list = [None]

            check_item_path_list = []
            for group_name in group_name_list:
                if group_name is not None:
                    curr_check_dir = f'{check_dir}/{group_name}'

                curr_check_item_path_list = [str(x) for x in Path(curr_check_dir).glob(f'*.{check_type}')]
                check_item_path_list.extend(curr_check_item_path_list)

            existed_item_stem_list = [Path(x).stem for x in check_item_path_list]

            curr_path_info_list = [x for x in curr_path_info_list if Path(
                x[first_path_name]).stem not in existed_item_stem_list]

    filter_existed_num = len(curr_path_info_list)

    if input_name is not None:
        curr_path_info_list = [x for x in curr_path_info_list if input_name in x[first_path_name]]

    if input_num > 0:
        curr_path_info_list = curr_path_info_list[:input_num]

    actual_num = len(curr_path_info_list)

    print(f'{data_name} -- total_num: {total_num}, filter_existed_num: {filter_existed_num}, actual_num: {actual_num}')

    return curr_path_info_list


def get_path_info_list(config, read_data_config):
    path_info_list = []

    tmp_path_info = {}
    for key, value in config.items():
        if key == 'data':
            continue

        tmp_path_info[key] = value

    first_read_config = read_data_config[0]
    first_type = first_read_config['type']
    first_path_name = first_read_config['path_name']

    curr_path_info_list = []
    config_data = config['data']
    for data_name, data_item in config_data.items():
        raw_group_mode = get_config_item(data_item, tmp_path_info, 'group_mode', default_value=False)
        group_mode = raw_group_mode

        selected_group_name_list = get_config_item(data_item, tmp_path_info, 'group_name', default_value=[])

        first_dir_name = first_read_config['dir_name']
        first_dir = data_item[first_dir_name]

        if group_mode:
            group_name_list = [x.name for x in Path(first_dir).glob('*') if x.is_dir()]

            if len(selected_group_name_list) > 0:
                group_name_list = [x for x in group_name_list if x in selected_group_name_list]

        else:
            group_name_list = [None]

        for group_name in group_name_list:
            group_path_info_list = handle_one_group_name(read_data_config, tmp_path_info, data_item, group_name)
            curr_path_info_list.extend(group_path_info_list)

        curr_path_info_list = adjust_path_info_list(read_data_config, data_name, data_item, tmp_path_info,
                                                    curr_path_info_list, first_path_name, group_mode, selected_group_name_list)

        path_info_list.extend(curr_path_info_list)

    return path_info_list
