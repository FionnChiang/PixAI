import os
import argparse
import json

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from imgutils.tagging.pixai import get_pixai_tags

import re



def is_sexual_tag(tag: str) -> bool:
    tag = tag.lower()
    return 

def main():
    parser = argparse.ArgumentParser(description="批量识别图片tag，并保存结果")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tags", nargs='+', help="指定保留的general tag列表")
    group.add_argument("--config", type=str, help="配置文件路径 (JSON格式，数组)")
    parser.add_argument("--output", type=str, default="tags_result.json", help="结果输出文件 (JSON格式)")
    args = parser.parse_args()

    keep_list = None
    if args.tags:
        keep_list = args.tags
    elif args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            keep_list = json.load(f)
        if not isinstance(keep_list, list):
            print("配置文件格式错误，应为JSON数组")
            return

    script_dir = os.path.dirname(__file__)
    img_dir = os.path.join(script_dir, "figure/swd")
    img_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    SEXUAL_ROOTS = [
        "nipple", "pussy", "ass", "breast", "cameltoe", "thong", "slip",
        "see_through", "wet", "open", "lift", "sideboob", "underboob",
        "garter", "cleavage", "bare", "micro", "highleg", "string",
        "o_ring", "bondage", "leotard"
    ]
    
    
    results = []
    for img in img_files:
        img_path = os.path.join(img_dir, img)
        general_tags, character_tags = get_pixai_tags(img_path, model_name='v0.9',thresholds={'general':0.6, 'character':0.6})
        if keep_list is not None:
            general_tags = [tag for tag in general_tags if any(root in tag.lower() for root in SEXUAL_ROOTS)]
            general_tags = [tag for tag in general_tags if tag in keep_list]
        else:
            general_tags = [tag for tag in general_tags if any(root in tag.lower() for root in SEXUAL_ROOTS)]
        results.append({
            "image": img,
            "general_tags": general_tags,
            "character_tags": list(character_tags.keys())
        })

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("处理完成，结果保存在:", args.output)
    
    


if __name__ == "__main__":
    main()