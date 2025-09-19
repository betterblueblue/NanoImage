from __future__ import annotations
from typing import Dict, List

NEGATIVE_DEFAULT = "请避免：水印、文字、畸形手指或肢体、过度锐化、过饱和、过曝、明显噪点。"


def build_prompt(template: str, params: Dict) -> str:
    try:
        text = template.format(**(params or {}))
    except Exception:
        text = template
    if params.get("negatives"):
        text += " " + str(params["negatives"])
    else:
        text += " " + NEGATIVE_DEFAULT
    return text


TEMPLATES = {
    "figurine": (
        "将这张图片转为精致的角色手办风格，后方摆放印有角色图像的盒子，"
        "盒子上显示一台电脑屏幕展示 Blender 建模界面；前景添加圆形塑料底座，"
        "角色站在其上；室内布光，写实质感，细节清晰，4k。"
    ),
    "era_style": (
        "将角色的风格改为{era}年代的经典{gender}风格。"
        "添加{hair}，{face}，将背景改为标志性的{backdrop}。"
        "不要改变角色的面部，保持原始五官与身份不变，写实摄影风格，质感自然。"
    ),
    "enhance": (
        "增强照片对比度、色彩与光线层次，可适度裁剪、移除破坏构图的干扰元素，"
        "整体更有层次与质感，但保持自然不过度饱和。"
    ),
    "old_photo_restore": (
        "修复破损、划痕与噪点，并进行自然上色，保持时代质感与面部细节，"
        "不要改变人物特征。"
    ),
    "id_photo": (
        "截取人物头肩部并居中排版，制作 2 寸证件照：蓝底、职业正装、正脸、自然微笑，"
        "光线均匀，背景纯色无阴影。"
    ),
}

HAIRSTYLES: List[str] = [
    "短发清爽", "中长直发", "空气刘海", "大波浪卷", "高马尾", "丸子头", "油头背梳", "层次短发", "波波头",
]

