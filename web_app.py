import os
import re
import sqlite3
from flask import Flask, request, session, redirect, url_for, render_template_string

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
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        query2 = request.form.get('query2', '').strip()
        logic = request.form.get('logic', 'AND')
        if query:
            results = search_database(query, extra_query=query2, operator=logic)
            session['results'] = results
            session['query'] = query
            # 重定向到查看页面，从第一张开始
            return redirect(url_for('view_image', index=0))
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
        </script>
      </head>
      <body>
        <h1>输入查询描述</h1>
        <form method="post">
          <input type="text" name="query" placeholder="请输入查询描述">
          <button type="button" onclick="toggleAdvanced()">增加搜索关键词</button>
          <div id="advancedSearch" style="display:none; margin-top:10px;">
            <input type="text" name="query2" placeholder="请输入额外搜索描述">
            <select name="logic">
              <option value="AND">AND</option>
              <option value="OR">OR</option>
            </select>
          </div>
          <input type="submit" value="查询">
        </form>
      </body>
    </html>
    ''')

# 显示图片页面，根据索引显示上一张或下一张
@app.route('/view')
def view_image():
    results = session.get('results', [])
    query = session.get('query', '')
    try:
        index = int(request.args.get('index', 0))
    except ValueError:
        index = 0
    total = len(results)
    if total == 0:
        return f'<p>未找到与 "{query}" 相关的图片。</p><p><a href="{url_for("index")}">返回查询</a></p>'
    # 保证索引在合法范围内
    if index < 0: index = 0
    if index >= total: index = total - 1
    image = results[index]
    # 构造上一张和下一张按钮链接
    prev_index = index - 1 if index > 0 else 0
    next_index = index + 1 if index < total - 1 else total - 1
    return render_template_string('''
    <!doctype html>
    <html>
      <head>
        <title>图片浏览</title>
      </head>
      <body>
        <h1>查询结果：{{ query }}</h1>
        <p>显示 {{ current + 1 }} / {{ total }} 张</p>
        <div style="text-align:center; margin-top:20px;">
          {% if current > 0 %}
            <a href="{{ url_for('view_image', index=prev) }}">上一张</a>
          {% endif %}
          {% if current < total - 1 %}
            <a href="{{ url_for('view_image', index=next) }}">下一张</a>
          {% endif %}
        </div>
        <div style="text-align:center; margin-top:20px;">
          <a href="{{ url_for('index') }}">重新查询</a>
        </div>
        <div style="width:800px; height:600px; border:1px solid #ccc; display:flex; justify-content:center; align-items:center; margin:auto;">
          <img src="{{ url_for('static', filename=image) }}" alt="Image" style="max-width:100%; max-height:100%; object-fit:contain;">
        </div>
        
      </body>
    </html>
    ''', query=query, image=image, current=index, total=total, prev=prev_index, next=next_index)

if __name__ == '__main__':
    # 监听所有可用IP以方便局域网访问
    app.run(host='0.0.0.0', port=5000, debug=True)
