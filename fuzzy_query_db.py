import sqlite3
import json
import os


def create_database(db_path="tags.db", json_path="tags_result.json"):
    # 如果数据库已存在，则删除重新创建，确保数据最新
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 创建数据表
    cursor.execute("CREATE TABLE tags (image TEXT, tag TEXT)")

    # 加载 JSON 数据
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 判断 JSON 格式是否为列表或者包含 images 键
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "images" in data:
        items = data["images"]
    else:
        print("未知的 JSON 格式")
        return

    # 将每个图片的标签插入数据库
    for item in items:
        image = item.get("image", "")
        # 合并 general_tags 与 character_tags
        all_tags = item.get("general_tags", []) + item.get("character_tags", [])
        for tag in all_tags:
            cursor.execute("INSERT INTO tags (image, tag) VALUES (?, ?)", (image, tag))

    conn.commit()
    conn.close()
    print(f"数据库已创建，路径: {db_path}")


def search_database(query, db_path="tags.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 如果查询为'ass'（区分大小写，统一转换为小写处理），则排除仅包含'glasses'的标签
    if query.lower() == 'ass':
        cursor.execute("SELECT DISTINCT image FROM tags WHERE tag LIKE ?", ('\\bass\\b',))
    else:
        pattern = f"%{query}%"
        cursor.execute("SELECT DISTINCT image FROM tags WHERE tag LIKE ?", (pattern,))
    results = cursor.fetchall()
    conn.close()
    # 返回图片文件名列表
    return [r[0] for r in results]


def main():
    db_path = "tags.db"
    # 如果数据库不存在则先创建
    if not os.path.exists(db_path):
        create_database(db_path=db_path)
    
    print("数据库已就绪，可以进行模糊查询。")
    while True:
        query = input("请输入描述（直接回车退出）：").strip()
        if not query:
            break
        images = search_database(query, db_path=db_path)
        if images:
            print("匹配到的图片：", images)
        else:
            print("未匹配到相关图片。")


if __name__ == "__main__":
    main()
