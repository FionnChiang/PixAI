import json
from collections import Counter


def generate_top_tags(input_file="tags_result.json", output_file="top30_tags.json", top_n=30):
    # 读取tags_result.json文件
    with open(input_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    counter = Counter()
    # 遍历每个图片的tag，统计出现次数
    for item in results:
        # 合并 general_tags 和 character_tags
        tags = item.get("general_tags", [])
        counter.update(tags)

    # 获取出现次数最高的top_n个tag
    top_tags = [tag for tag, count in counter.most_common(top_n)]

    # 保存为配置文件（JSON格式）
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(top_tags, f, indent=2, ensure_ascii=False)

    print(f"生成配置文件 {output_file}，包含出现次数最高的 {top_n} 个TAG。")


if __name__ == "__main__":
    generate_top_tags()
