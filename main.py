import folder_tagger
import web_app
import fuzzy_query_db
import generate_top_tags
import os



if __name__ == "__main__":
    if not os.path.exists("tags.db"):
        folder_tagger.get_tags()
        fuzzy_query_db.create_database()
        # 生成 top tags 列表
    generate_top_tags.generate_top_tags()
    web_app.app.run(host='127.0.0.1', port=5000)