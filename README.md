# Agent-based Video Trimming

> [**Agent-based Video Trimming**]() <br>
> Lingfeng Yang<sup>1†</sup>, Zhenyuan Chen<sup>2†</sup>, Xiang Li<sup>3,2∗</sup>, Peiyang Jia<sup>4</sup>, Liangqu Long<sup>4</sup>, Jian Yang<sup>1∗</sup>  <br>
> <sup>1</sup>Nanjing University of Science and Technology, <sup>2</sup>VCIP, CS, Nankai University, <sup>3</sup>NKIARI, Shenzhen Futian, <sup>4</sup>Insta360<br>
> `{yanglfnjust, csjyang}@njust.edu.cn, zhenyuanchen@mail.nankai.edu.cn,`  <br>
> `xiang.li.implus@nankai.edu.cn, jiapeiyang@insta360.com, liangqu.long@gmail.com`<br>
> [[Arxiv](https://arxiv.org/abs/2412.09513)] [[Project Page](https://ylingfeng.github.io/AVT/)] [[Demo](https://huggingface.co/spaces/ylingfeng/Agent-based_Video_Trimming)]

<hr />


<p align="center">
    <img src="./assets/video_trimming.svg" alt="video_trimming" style="width: 50%;">
    <div style="text-align: center; color: gray; font-size: 13px;">
        A comparison between our new task and existing video tasks: (a) Highlight Detection retrieves clips above a saliency threshold. (b) Moment Retrieval identifies the start and end for intervals related to a given query. (c) Video Summarization extracts keyframes for each theme of the video. (d) Video Trimming addresses more than just a retrieval task by also filtering wasted footage and logically composing the selected segments.
    </div>
</p>

<p align="center">
    <img src="./assets/framework.svg" alt="framework" style="width: 100%;">
    <div style="text-align: center; color: gray; font-size: 13px;">
        The overall framework of AVT. The approach first (a) converts sampled video content into structured captions and attributes, then (b) discards defective clips, and finally (c) organizes the remaining clips into a coherent final cut.
    </div>
</p>

## 🛠 Data Preparation
<pre>
data
├── avt
│   ├── caption
│   ├── output
│   │   ├── caption
│   │   ├── evaluation
│   │   └── story
│   ├── section_data
│   └── video
│        ├── daily_life-family-CapperCoolCooper
│        │   └── KRqR6LSoP8.mp4
│        ├── daily_life-family-Earls_Family_Vlogs
│        │   └── MyLwV1V19WY.mkv
│         ...
├── youtube_highlights
│   │    
│    ...
└── tvsum
    │   
     ...
</pre>

## 🚀 How to start
#### Get Section Data

```bash
python tools/get_section_data.py --config data/avt/get_section_data.yaml
```
This command would generate `./data/avt/section_data`.

#### Video Structuring

```bash
python tools/get_caption.py --config data/avt/get_caption.yaml
```
This command would generate `./data/avt/caption`.

#### Story Composition

```bash
python tools/get_story.py --config data/avt/get_story.yaml
```
This command would generate `./data/avt/output/caption` and `./data/avt/output/story`.

#### Output Video

```bash
python tools/get_video.py --config data/avt/get_video.yaml
```
This command would generate `./data/avt/output/story/*/output_video.mp4`.

#### Video Evaluation

```bash
python tools/get_evaluation.py --config data/avt/get_evaluation.yaml
```
This command would generate `./data/avt/output/evaluation`.

## 🎥 Visualization 
<p align="center">
    <img src="./assets/visualization.svg" alt="visualization" style="width: 100%;">
    <div style="text-align: center; color: gray; font-size: 13px;">
        Visualization of trimmed videos on the video trimming dataset. AVT creates a more complete storyline with more highlight footage and less wasted footage.
    </div>
</p>

Checkout the videos on our [project page](https://ylingfeng.github.io/AVT/) :)

## ⭐ Citation
If you find our paper or repo helpful for your research, please consider citing the following paper and giving this repo a star. Thank you!

```
@article{avt,
  title={Agent-based Video Trimming},
  author={Yang, Lingfeng and Chen, Zhenyuan and Li, Xiang and Jia, Peiyang and Long, Liangqu and Yang, Jian},
  journal={arXiv preprint arXiv:2412.09513},
  year={2024}
}
```
