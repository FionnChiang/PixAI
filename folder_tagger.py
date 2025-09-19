import os
import json
from tqdm import tqdm
import re
import random
import shutil

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from imgutils.tagging.pixai import get_pixai_tags


def get_tags(keep_list=None, output="tags_result.json", full=False):
    """
    批量识别图片tag，并保存结果。

    参数:
      keep_list: list 或 None - 指定保留的 general tag 列表，若为 None 则使用内置判断（sexual tags）
      output: str - 结果输出的 JSON 文件名
      full: bool - 若为 True，则全部重新 tag；否则，仅处理 figure 目录中新增加的图片，且更新删除了的图片记录
    """
    if keep_list is not None and not isinstance(keep_list, list):
        print("keep_list 需要为列表类型")
        return

    script_dir = os.path.dirname(__file__)
    img_dir = os.path.join(script_dir, "figure")
    img_files = []
    for root, dirs, files in os.walk(img_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, script_dir).replace("\\", "/")
                img_files.append(rel_path)

    # 如果不全量处理且输出文件存在，则只处理新图片，
    # 同时先剔除已记录中不在当前img_files中的数据（被删除的图片）
    existing_results = []
    processed_set = set()
    if not full and os.path.exists(output):
        try:
            with open(output, "r", encoding="utf-8") as f:
                existing_results = json.load(f)
            # 过滤掉已删除的图片记录
            existing_results = [entry for entry in existing_results if entry["image"] in img_files]
            processed_set = {entry["image"] for entry in existing_results}
        except Exception as e:
            print(f"加载已有输出 {output} 失败，将重新处理全部图片: {e}")
            existing_results = []
            processed_set = set()

    SEXUAL_ROOTS = [
        "nipple", "pussy", "ass", "breast", "cameltoe", "thong", "slip",
        "see_through", "wet", "open", "lift", "sideboob", "underboob",
        "garter", "cleavage", "bare", "micro", "highleg",
        "o_ring", "bondage", "leotard", "crotch", "exposed", "panty",
        "anal", "anus", "censored", "panties", "maid", "smell", "cum", 
        "sit", "straddling", "face"
    ]

    new_results = []
    Add_cnt = 0
    for img in tqdm(img_files, desc="Processing images"):
        if img in processed_set:
            continue

        img_path = os.path.join(script_dir, img)
        try:
            general_tags, character_tags = get_pixai_tags(
                img_path, model_name='v0.9',
                thresholds={'general': 0.3, 'character': 0.6}
            )
        except Exception as e:
            print(f"处理图片 {img} 时出错: {e}")
            # 错误处理：将处理失败的图片移动到 figure/error 目录下，并重命名为 img_error_{随机8位数字}{原扩展名}
            error_dir = os.path.join(script_dir, "figure", "error")
            if not os.path.exists(error_dir):
                os.makedirs(error_dir)
            ext = os.path.splitext(img)[1]
            attempt = 0
            while True:
                random_number = str(random.randint(0, 10000000)).zfill(8)
                new_filename = f"img_error_{random_number}{ext}"
                new_file_path = os.path.join(error_dir, new_filename)
                if not os.path.exists(new_file_path):
                    break
                attempt += 1
                if attempt > 10:
                    break
            try:
                os.rename(img_path, new_file_path)
                rel_new_path = os.path.relpath(new_file_path, script_dir).replace("\\", "/")
                print(f"已将错误文件 {img} 重命名为 {rel_new_path}")
            except Exception as rename_e:
                print(f"重命名错误文件 {img} 失败: {rename_e}")
            continue

        if keep_list is not None:
            general_tags = [tag for tag in general_tags if any(root in tag.lower() for root in SEXUAL_ROOTS)]
            general_tags = [tag for tag in general_tags if tag in keep_list]
        else:
            general_tags = [tag for tag in general_tags if any(root in tag.lower() for root in SEXUAL_ROOTS)]

        new_results.append({
            "image": img,
            "general_tags": general_tags,
            "character_tags": list(character_tags.keys())
        })
        Add_cnt += 1

    print(f"新增处理图片数量: {Add_cnt}")

    # 合并之前的数据与新增数据
    all_results = existing_results + new_results
    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print("处理完成，结果保存在:", output)


if __name__ == "__main__":
    # 测试调用：仅更新新增图片（同时删除已不存在的图片记录）
    get_tags(full=False)