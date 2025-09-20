import os
import re
import sqlite3
import random
import json
from flask import Flask, request, session, redirect, url_for, render_template_string, send_file, jsonify
import folder_tagger
import fuzzy_query_db
import generate_top_tags

# 设置 Flask 应用，静态文件目录为 figure 文件夹
app = Flask(__name__, static_folder='/', static_url_path='/')
app.secret_key = 'your_secret_key'  # 请更换为随机的密钥以提高安全性
app.config['SESSION_TYPE'] = 'filesystem'

DB_PATH = os.path.join(os.path.dirname(__file__), 'tags.db')

# 辅助函数：根据查询描述从数据库中模糊匹配图片
def regexp(expr, item):
    if item is None:
        return False
    return re.search(expr, item.lower()) is not None

def search_database(query, extra_query=None, operator="AND", db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.create_function("REGEXP", 2, regexp)
    cursor = conn.cursor()
    if extra_query and extra_query.strip():
        if query.lower()=='ass' or extra_query.lower()=='ass':
            if query.lower()=='ass' and extra_query.lower()=='ass':
                cursor.execute("SELECT DISTINCT image FROM tags WHERE LOWER(tag) REGEXP ? AND LOWER(tag) NOT LIKE ?", ("\\bass\\b", "%glasses%"))
            else:
                # 判断哪个查询词是'ass'、哪个是其他查询词
                if query.lower()=='ass':
                    term_ass = query
                    term_other = extra_query
                else:
                    term_ass = extra_query
                    term_other = query
                pattern_other = f"%{term_other}%"
                cursor.execute("""
                    SELECT image FROM tags
                    WHERE ( (LOWER(tag) REGEXP ? AND LOWER(tag) NOT LIKE ?) OR tag LIKE ? )
                    GROUP BY image
                    HAVING SUM(CASE WHEN LOWER(tag) REGEXP ? AND LOWER(tag) NOT LIKE ? THEN 1 ELSE 0 END) > 0
                       AND SUM(CASE WHEN tag LIKE ? THEN 1 ELSE 0 END) > 0
                """, ("\\bass\\b", "%glasses%", pattern_other, "\\bass\\b", "%glasses%", pattern_other))
        else:
            pattern1 = f"%{query}%"
            pattern2 = f"%{extra_query}%"
            if operator.upper() == "AND":
                cursor.execute("""
                    SELECT image FROM tags
                    WHERE tag LIKE ? OR tag LIKE ?
                    GROUP BY image
                    HAVING SUM(CASE WHEN tag LIKE ? THEN 1 ELSE 0 END) > 0
                       AND SUM(CASE WHEN tag LIKE ? THEN 1 ELSE 0 END) > 0
                """, (pattern1, pattern2, pattern1, pattern2))
            else:
                cursor.execute("SELECT DISTINCT image FROM tags WHERE tag LIKE ? OR tag LIKE ?", (pattern1, pattern2))
    else:
         if query.lower() == 'ass':
             cursor.execute("SELECT DISTINCT image FROM tags WHERE LOWER(tag) REGEXP ? AND LOWER(tag) NOT LIKE ?", ("\\bass\\b", "%glasses%"))
         else:
             pattern = f"%{query}%"
             cursor.execute("SELECT DISTINCT image FROM tags WHERE tag LIKE ?", (pattern,))
    results = cursor.fetchall()
    conn.close()
    # 返回图片文件名列表
    return [r[0] for r in results]

# 首页，显示查询表单
@app.route('/', methods=['GET', 'POST'])
def index():
    # 读取热门标签
    top_tags = []
    try:
        top_tags_path = os.path.join(os.path.dirname(__file__), "top30_tags.json")
        with open(top_tags_path, "r", encoding="utf-8") as f:
            top_tags = json.load(f)
    except Exception as e:
        print(f"读取热门标签失败: {e}")
    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        query2 = request.form.get('query2', '').strip()
        logic = request.form.get('logic', 'AND')
        # 判断是否要随机排序
        random_order = request.form.get('random', '')
        seed = ""
        if random_order == '1':
            # 生成随机种子
            seed = random.randint(0, 10000000)
        if query:
            # 将 seed 作为参数传递
            return redirect(url_for('view_image', query=query, query2=query2, logic=logic, index=0, seed=seed))
    return render_template_string('''
    <!doctype html>
    <html>
      <head>
        <title>图片查询</title>
        <script>
          function toggleAdvanced() {
            var adv = document.getElementById("advancedSearch");
            adv.style.display = (adv.style.display === "none" ? "block" : "none");
          }
          function updateTags() {
            if (!confirm("确定要更新图片标签吗？")) return;
            fetch('/update_tags', {method: 'POST'})
              .then(resp => resp.json())
              .then(data => {
                alert(data.msg);
                if (data.success) location.reload();
              })
              .catch(err => alert("更新失败: " + err));
          }
        </script>
      </head>
      <body>
        <h1>输入查询描述</h1>
        <button onclick="updateTags()">更新图片标签</button>
        <form method="post">
          <input type="text" name="query" placeholder="请输入查询描述"><br>
          <button type="button" onclick="toggleAdvanced()">增加搜索关键词</button><br>
          <div id="advancedSearch" style="display:none; margin-top:10px;">
            <input type="text" name="query2" placeholder="请输入额外搜索描述">
            <select name="logic">
              <option value="AND">AND</option>
              <option value="OR">OR</option>
            </select>
          </div>
          <div>
            <label>
              <input type="checkbox" name="random" value="1">
              随机排序
            </label>
          </div>
          <input type="submit" value="查询">
        </form>
        <hr>
        <h2>当前热门Tag</h2>
        <ul>
          {% for tag in top_tags %}
            <li>{{ tag }}</li>
          {% endfor %}
        </ul>
      </body>
    </html>
    ''', top_tags=top_tags)

# 显示图片页面，根据索引显示上一张或下一张
@app.route('/view')
def view_image():
    query = request.args.get('query', '')
    query2 = request.args.get('query2', '')
    logic = request.args.get('logic', 'AND')
    try:
        index = int(request.args.get('index', 0))
    except ValueError:
        index = 0

    # 根据查询参数重新获取结果数据
    results = search_database(query, extra_query=query2, operator=logic) if query else []

    # 如果存在 seed 参数，则基于种子进行确定性随机排序
    seed_value = request.args.get('seed', '')
    if seed_value:
        try:
            seed_int = int(seed_value)
            r = random.Random(seed_int)
            r.shuffle(results)
        except Exception as e:
            print(f"随机排序出错: {e}")

    total = len(results)
    if total == 0:
        return f'<p>未找到与 "{query}" 相关的图片。</p><p><a href="{url_for("index")}">返回查询</a></p>'

    # 限制索引范围
    if index < 0:
        index = 0
    if index >= total:
        index = total - 1

    # 当前显示图片
    image = results[index]

    # 将整个结果列表传给前端（前端控制切换效果）
    return render_template_string('''
    <!doctype html>
    <html>
      <head>
        <title>图片浏览</title>
        <style>
          #nav-buttons { text-align: center; margin-top: 20px; }
          #nav-buttons button { margin: 0 10px; }
          #current_count { margin-top: 10px; text-align: center; }
          #img-container { display: flex; justify-content: center; align-items: center; margin: auto; width: 800px; height: 600px; border: 1px solid #ccc;}
          #img-container img { max-width: 100%; max-height: 100%; object-fit: contain; }
        </style>
      </head>
      <body>
        <h1 style="text-align: center;">查询结果：{{ query }}</h1>
        <div id="current_count" style="text-align: center;">{{ index + 1 }} / {{ total }}</div>
        <div id="img-container">
            <img id="current_image" src="{{ url_for('static', filename=image) }}" alt="Image">
        </div>
        <div id="nav-buttons">
          <button id="prevBtn" {% if index == 0 %}disabled{% endif %}>上一张</button>
          <button id="nextBtn" {% if index == total - 1 %}disabled{% endif %}>下一张</button>
          <button onclick="location.href='{{ url_for('index') }}'">重新查询</button>
          <button id="downloadBtn">打包下载</button>
        </div>
        <!-- 添加一个隐藏的 iframe 用于触发下载 -->
        <iframe id="downloadIframe" style="display:none;"></iframe>

        <script>
          // 后端传递的查询结果列表
          var results = {{ results | tojson }};
          var currentIndex = {{ index }};
          var total = {{ total }};
          // 静态目录根，相当于url_for('static', filename='')，末尾包含斜杠
          var baseUrl = "{{ url_for('static', filename='') }}";
          var bufferEnd = 0;
          // 显示某一索引的图片
          function showImage(idx) {
            if (idx < 0) idx = 0;
            if (idx >= total) idx = total - 1;
            currentIndex = idx;
            document.getElementById("current_image").src = baseUrl + results[idx];
            document.getElementById("current_count").innerText = (currentIndex + 1) + " / " + total;
            // 更新按钮状态
            document.getElementById("prevBtn").disabled = (currentIndex === 0);
            document.getElementById("nextBtn").disabled = (currentIndex === total - 1);
            // 预加载后续最多16张图片
            for (var i = bufferEnd + 1; i < Math.min(idx + 17, total); i++) {
              var img = new Image();
              img.src = baseUrl + results[i];
            }
            bufferEnd = Math.min(idx + 16, total - 1);
          }

          document.getElementById("prevBtn").addEventListener("click", function() {
            showImage(currentIndex - 1);
          });
          document.getElementById("nextBtn").addEventListener("click", function() {
            showImage(currentIndex + 1);
          });

          // 为“打包下载”按钮绑定点击事件，将请求发送给隐藏 iframe
          document.getElementById("downloadBtn").addEventListener("click", function(){
              var downloadUrl = "{{ url_for('download_zip', query=query, query2=query2, logic=logic, seed=seed) }}";
              document.getElementById("downloadIframe").src = downloadUrl;
          });
        </script>
      </body>
    </html>
    ''', query=query,query2=query2,logic=logic,seed=seed_value, image=image, index=index, total=total, results=results)

# 下载 ZIP 包接口
@app.route('/download_zip')
def download_zip():
    query = request.args.get('query', '')
    query2 = request.args.get('query2', '')
    logic = request.args.get('logic', 'AND')
    seed_value = request.args.get('seed', '')
    results = search_database(query, extra_query=query2, operator=logic) if query else []
    # 如果存在 seed，则使用确定性随机排序
    if seed_value:
        try:
            seed_int = int(seed_value)
            r = random.Random(seed_int)
            r.shuffle(results)
        except Exception as e:
            print(f"随机排序出错: {e}")
    # 创建 zip 包
    import zipfile, io
    from datetime import datetime
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        script_dir = os.path.dirname(__file__)
        for img in results:
            file_path = os.path.join(script_dir, img)
            if os.path.exists(file_path):
                zf.write(file_path, arcname=os.path.basename(img))
    memory_file.seek(0)
    # 生成压缩包文件名：{tags}_{time}.zip
    tag_str = query if query else "all"
    if query2:
        tag_str += "_" + query2
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    zip_filename = f"{tag_str}_{timestamp}.zip"
    return send_file(memory_file, as_attachment=True, download_name=zip_filename)

@app.route('/update_tags', methods=['POST'])
def update_tags():
    try:
        # 只处理新增图片和删除已不存在图片的记录
        folder_tagger.get_tags(full=False)
        # 重新生成数据库和热门标签
        fuzzy_query_db.create_database()
        generate_top_tags.generate_top_tags()
        return jsonify({'success': True, 'msg': '图片标签已更新！'})
    except Exception as e:
        return jsonify({'success': False, 'msg': f'更新失败: {e}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
