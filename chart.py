from flask import Flask, render_template_string, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

# ==========================================
# 0. データ管理 (簡易DB)
# ==========================================
app_config = {
    "title": "ROOM×RTS イベントプラン",
    "subtitle": "プロジェクト進捗管理ダッシュボード"
}

# タスクデータ
tasks_db = [
    {"id": 1, "assignee": "佐藤", "name": "企画立案", "start": "2026-03-09", "end": "2026-03-13", "progress": 100},
    {"id": 2, "assignee": "鈴木", "name": "会場選定・予約", "start": "2026-03-11", "end": "2026-03-18", "progress": 80},
    {"id": 3, "assignee": "田中", "name": "出演者オファー", "start": "2026-03-13", "end": "2026-03-23", "progress": 40},
    {"id": 4, "assignee": "高橋", "name": "広報・SNS運用", "start": "2026-03-18", "end": "2026-04-02", "progress": 10},
    {"id": 5, "assignee": "伊藤", "name": "当日運営マニュアル作成", "start": "2026-03-28", "end": "2026-04-05", "progress": 0},
]

# ==========================================
# 1. デザインとレイアウト (HTML/CSS/JS)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.title }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* --- ベースデザイン (ライトモード) --- */
        :root {
            --bg-color: #f7f9fc;
            --panel-color: #ffffff;
            --text-main: #2c3e50;
            --text-sub: #7f8c8d;
            --border-color: #e2e8f0;
            --accent-color: #3498db;
            
            --color-done: #2ecc71;
            --color-wip: #3498db;
            --color-todo: #f1c40f;
            --color-danger: #e74c3c;
            
            /* 曜日カラー */
            --sat-color: #eaf4ff; /* 土曜背景 */
            --sun-color: #ffeaea; /* 日曜背景 */
            --mon-border: #bdc3c7; /* 月曜区切り線 */
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 40px;
        }

        /* --- タイトル編集エリア --- */
        .header-container {
            margin-bottom: 30px;
        }
        
        .editable-title-wrapper {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        h1 {
            text-align: left;
            font-size: 2rem;
            font-weight: 800;
            color: #2c3e50;
            margin: 0;
            letter-spacing: -0.5px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: border-color 0.2s;
        }
        h1:hover {
            border-bottom: 2px dashed #cbd5e0;
        }
        
        .subtitle {
            text-align: left;
            color: var(--text-sub);
            margin-top: 5px;
            font-weight: 500;
            cursor: pointer;
        }

        #title-form {
            display: none;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
        }
        .form-row {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        .form-row input {
            flex: 1;
        }

        h2 {
            font-size: 1.2rem;
            margin-bottom: 15px;
            color: #34495e;
            border-left: 4px solid var(--accent-color);
            padding-left: 10px;
        }

        .card {
            background-color: var(--panel-color);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }

        /* --- ガントチャートエリア --- */
        .gantt-scroll-wrapper {
            overflow-x: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            position: relative;
            /* 横スクロール可能な幅を確保 */
            min-width: 100%;
        }
        
        .timeline-header {
            display: flex;
            background-color: #f8fafc;
            border-bottom: 1px solid var(--border-color);
            /* 日数×列幅（35px）で最低幅を計算し、CSSで確保 */
            min-width: {{ total_days * 35 + 300 }}px; 
            position: sticky;
            top: 0;
            z-index: 20;
        }
        
        /* 固定列ラッパー */
        .sticky-col-header {
            position: sticky;
            left: 0;
            z-index: 30;
            display: flex;
            background-color: #f8fafc;
            box-shadow: 2px 0 5px rgba(0,0,0,0.05);
        }

        .assignee-header {
            width: 80px;
            padding: 12px 10px;
            font-weight: 600;
            color: #555;
            border-right: 1px solid var(--border-color);
            text-align: center;
            flex-shrink: 0;
        }

        .task-name-header {
            width: 220px;
            padding: 12px 15px;
            font-weight: 600;
            color: #555;
            border-right: 1px solid var(--border-color);
            flex-shrink: 0;
        }

        .timeline-days {
            flex-grow: 1;
            display: flex;
        }

        .day-marker {
            flex: 1;
            text-align: center;
            font-size: 0.75rem;
            padding: 8px 0;
            border-left: 1px solid var(--border-color);
            color: var(--text-sub);
            min-width: 35px; /* 1日の最小幅 */
            box-sizing: border-box;
        }
        .day-marker.sat { background-color: var(--sat-color); color: #3498db; }
        .day-marker.sun { background-color: var(--sun-color); color: #e74c3c; }
        .day-marker.mon { border-left: 2px solid var(--mon-border); }

        .task-row {
            display: flex;
            border-bottom: 1px solid var(--border-color);
            height: 44px;
            align-items: center;
            /* ヘッダーと同じ幅を確保 */
            min-width: {{ total_days * 35 + 300 }}px;
            position: relative;
        }
        .task-row:hover { background-color: #f8f9fa; }

        /* 固定列データ */
        .sticky-col-data {
            position: sticky;
            left: 0;
            z-index: 10;
            display: flex;
            background-color: var(--panel-color);
            box-shadow: 2px 0 5px rgba(0,0,0,0.05);
            height: 100%;
            align-items: center;
        }

        .assignee-cell {
            width: 80px;
            padding: 0 10px;
            font-size: 0.85rem;
            text-align: center;
            border-right: 1px solid var(--border-color);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: #555;
            background-color: #fdfdfd;
            flex-shrink: 0;
        }

        .task-name {
            width: 220px;
            padding: 0 15px;
            font-size: 0.9rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            border-right: 1px solid var(--border-color);
            font-weight: 500;
            flex-shrink: 0;
        }

        .chart-area {
            flex-grow: 1;
            position: relative;
            height: 100%;
        }

        .grid-line {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 1px;
            background-color: #f1f5f9;
            z-index: 0;
            border-left: 1px solid var(--border-color);
            box-sizing: border-box;
        }
        .grid-line.sat { background-color: var(--sat-color); }
        .grid-line.sun { background-color: var(--sun-color); }
        .grid-line.mon { border-left: 2px solid var(--mon-border); }

        .gantt-bar {
            position: absolute;
            top: 10px;
            height: 24px;
            border-radius: 4px;
            z-index: 5;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            color: #fff;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 0 5px;
        }
        .gantt-bar:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            z-index: 100; /* ホバー時は最前面へ */
            overflow: visible; /* 文字が切れないように */
        }

        .status-done { background-color: var(--color-done); }
        .status-wip { background-color: var(--color-wip); }
        .status-todo { background-color: var(--color-todo); color: #555; }

        /* --- 編集テーブル --- */
        table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
        th { text-align: left; padding: 12px; color: var(--text-sub); font-weight: 600; border-bottom: 2px solid var(--border-color); }
        td { padding: 10px 12px; border-bottom: 1px solid var(--border-color); vertical-align: middle; }

        input[type="text"], input[type="date"], input[type="number"] {
            width: 100%; padding: 8px 10px; border: 1px solid #dcdcdc; border-radius: 6px;
            font-family: inherit; font-size: 0.9rem; box-sizing: border-box;
        }
        input:focus { outline: none; border-color: var(--accent-color); box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1); }

        .btn { padding: 10px 18px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-size: 0.9rem; }
        .btn-save { background-color: var(--accent-color); color: white; }
        .btn-save:hover { background-color: #2980b9; transform: translateY(-1px); }
        .btn-add { background-color: #f8f9fa; border: 1px dashed #cbd5e0; color: #555; width: 100%; margin-top: 15px; }
        .btn-add:hover { background-color: #e2e8f0; }
        .btn-delete { background-color: #fff0f0; color: var(--color-danger); padding: 6px 12px; font-size: 0.8rem; border: 1px solid #ffcccc; }
        .btn-delete:hover { background-color: #ffe6e6; }
        .btn-cancel { background-color: #95a5a6; color: white; margin-left: 10px; }

        .actions { display: flex; justify-content: flex-end; margin-top: 20px; border-top: 1px solid var(--border-color); padding-top: 20px; }
    </style>
</head>
<body>

    <!-- タイトル表示エリア -->
    <div class="header-container">
        <div id="title-display">
            <h1 onclick="toggleTitleEdit()" title="クリックして編集">{{ config.title }} ✎</h1>
            <div class="subtitle" onclick="toggleTitleEdit()">{{ config.subtitle }}</div>
        </div>

        <!-- タイトル編集フォーム -->
        <form id="title-form" action="/update_title" method="POST">
            <div class="form-row">
                <input type="text" name="title" value="{{ config.title }}" placeholder="タイトル" required>
            </div>
            <div class="form-row">
                <input type="text" name="subtitle" value="{{ config.subtitle }}" placeholder="サブタイトル">
            </div>
            <div style="text-align: right;">
                <button type="button" class="btn btn-cancel" onclick="toggleTitleEdit()">キャンセル</button>
                <button type="submit" class="btn btn-save">保存</button>
            </div>
        </form>
    </div>

    <!-- ガントチャートカード -->
    <div class="card">
        <h2>タイムライン (2026/03/09 〜 2026/07/31)</h2>
        <div class="gantt-scroll-wrapper">
            <div class="timeline-header">
                <!-- 固定列ヘッダー -->
                <div class="sticky-col-header">
                    <div class="assignee-header">担当</div>
                    <div class="task-name-header">タスク名</div>
                </div>
                
                <!-- 日付ヘッダー -->
                <div class="timeline-days">
                    {% for day in date_range %}
                        <div class="day-marker 
                            {% if day.weekday() == 5 %}sat{% endif %} 
                            {% if day.weekday() == 6 %}sun{% endif %}
                            {% if day.weekday() == 0 %}mon{% endif %}">
                            {{ day.strftime('%d') }}<br>
                            <span style="font-size:0.6rem;">{{ day.strftime('%m/%d') }}</span>
                        </div>
                    {% endfor %}
                </div>
            </div>

            {% for task in tasks %}
            <div class="task-row">
                <!-- 固定列データ -->
                <div class="sticky-col-data">
                    <div class="assignee-cell" title="{{ task.assignee }}">{{ task.assignee }}</div>
                    <div class="task-name" title="{{ task.name }}">{{ task.name }}</div>
                </div>

                <div class="chart-area">
                    <!-- グリッド線 -->
                    {% for day in date_range %}
                        <div class="grid-line 
                            {% if day.weekday() == 5 %}sat{% endif %} 
                            {% if day.weekday() == 6 %}sun{% endif %}
                            {% if day.weekday() == 0 %}mon{% endif %}" 
                            style="left: {{ loop.index0 * (100 / total_days) }}%;"></div>
                    {% endfor %}

                    <!-- バー -->
                    {% if task.visible %}
                    <div class="gantt-bar {{ task.status_class }}" 
                         style="left: {{ task.offset_percent }}%; width: {{ task.width_percent }}%;"
                         title="{{ task.name }} ({{ task.assignee }}): {{ task.progress }}%">
                        <span>{{ task.progress }}%</span>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- 編集カード -->
    <div class="card">
        <h2>タスク編集</h2>
        <form action="/update_tasks" method="POST">
            <table>
                <thead>
                    <tr>
                        <th style="width: 10%;">担当</th>
                        <th style="width: 30%;">タスク名</th>
                        <th style="width: 20%;">開始日</th>
                        <th style="width: 20%;">終了日</th>
                        <th style="width: 10%;">進捗(%)</th>
                        <th style="width: 10%;">操作</th>
                    </tr>
                </thead>
                <tbody id="task-list">
                    {% for task in tasks %}
                    <tr>
                        <input type="hidden" name="id[]" value="{{ task.id }}">
                        <td><input type="text" name="assignee[]" value="{{ task.assignee }}" placeholder="名前"></td>
                        <td><input type="text" name="name[]" value="{{ task.name }}" required></td>
                        <td><input type="date" name="start[]" value="{{ task.start }}" required></td>
                        <td><input type="date" name="end[]" value="{{ task.end }}" required></td>
                        <td><input type="number" name="progress[]" value="{{ task.progress }}" min="0" max="100"></td>
                        <td style="text-align: center;">
                            <button type="button" class="btn btn-delete" onclick="removeRow(this)">削除</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <button type="button" class="btn btn-add" onclick="addTask()">＋ タスクを追加</button>
            
            <div class="actions">
                <button type="submit" class="btn btn-save">変更を保存する</button>
            </div>
        </form>
    </div>

    <script>
        // タイトル編集の表示切替
        function toggleTitleEdit() {
            const display = document.getElementById('title-display');
            const form = document.getElementById('title-form');
            
            if (display.style.display === 'none') {
                display.style.display = 'block';
                form.style.display = 'none';
            } else {
                display.style.display = 'none';
                form.style.display = 'block';
            }
        }

        function getToday() {
            return new Date().toISOString().split('T')[0];
        }

        function addTask() {
            const tbody = document.getElementById('task-list');
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <input type="hidden" name="id[]" value="new">
                <td><input type="text" name="assignee[]" placeholder="担当"></td>
                <td><input type="text" name="name[]" placeholder="新しいタスク" required></td>
                <td><input type="date" name="start[]" value="2026-03-09" required></td>
                <td><input type="date" name="end[]" value="2026-03-13" required></td>
                <td><input type="number" name="progress[]" value="0" min="0" max="100"></td>
                <td style="text-align: center;">
                    <button type="button" class="btn btn-delete" onclick="removeRow(this)">削除</button>
                </td>
            `;
            tbody.appendChild(tr);
        }

        function removeRow(btn) {
            if(confirm('このタスクを削除しますか？')) {
                const row = btn.closest('tr');
                row.remove();
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# 2. ロジック (計算・データ操作)
# ==========================================

def process_tasks_for_gantt(tasks_data):
    """ガントチャート表示用の座標計算"""
    
    # 開始日を固定 (2026年3月9日)
    base_start_date = datetime(2026, 3, 9)
    # 終了日を固定 (2026年7月31日)
    base_end_date = datetime(2026, 7, 31)
    
    # タスクデータの処理
    processed = []
    
    for t in tasks_data:
        task = t.copy()
        try:
            task['start_dt'] = datetime.strptime(task['start'], '%Y-%m-%d')
            task['end_dt'] = datetime.strptime(task['end'], '%Y-%m-%d')
            processed.append(task)
        except ValueError:
            continue

    # 期間計算
    total_days = (base_end_date - base_start_date).days + 1
    date_range = [base_start_date + timedelta(days=x) for x in range(total_days)]

    # 座標計算
    for task in processed:
        start_offset = (task['start_dt'] - base_start_date).days
        duration = (task['end_dt'] - task['start_dt']).days + 1
        
        # 画面外(左側)にはみ出す場合の処理
        if start_offset + duration < 0:
            task['visible'] = False
        else:
            # 左にはみ出しているが一部見える場合
            if start_offset < 0:
                visible_duration = duration + start_offset
                task['offset_percent'] = 0
                task['width_percent'] = (visible_duration / total_days) * 100
            else:
                task['offset_percent'] = (start_offset / total_days) * 100
                task['width_percent'] = (duration / total_days) * 100
            
            task['visible'] = True

        # スタイル
        p = int(task['progress'])
        if p == 100: task['status_class'] = 'status-done'
        elif p > 0:  task['status_class'] = 'status-wip'
        else:        task['status_class'] = 'status-todo'

    return processed, date_range, total_days

# ==========================================
# 3. ルーティング
# ==========================================

@app.route('/')
def index():
    tasks, date_range, total_days = process_tasks_for_gantt(tasks_db)
    return render_template_string(HTML_TEMPLATE, 
                                  config=app_config,
                                  tasks=tasks, 
                                  date_range=date_range, 
                                  total_days=total_days)

# タイトル更新用
@app.route('/update_title', methods=['POST'])
def update_title():
    global app_config
    app_config['title'] = request.form.get('title')
    app_config['subtitle'] = request.form.get('subtitle')
    return redirect(url_for('index'))

# タスク更新用
@app.route('/update_tasks', methods=['POST'])
def update_tasks():
    global tasks_db
    
    ids = request.form.getlist('id[]')
    assignees = request.form.getlist('assignee[]')
    names = request.form.getlist('name[]')
    starts = request.form.getlist('start[]')
    ends = request.form.getlist('end[]')
    progresses = request.form.getlist('progress[]')
    
    new_tasks_db = []
    
    for i in range(len(ids)):
        task_id = ids[i]
        if task_id == 'new':
            task_id = len(tasks_db) + i + 1000
        else:
            task_id = int(task_id)
            
        new_tasks_db.append({
            "id": task_id,
            "assignee": assignees[i],
            "name": names[i],
            "start": starts[i],
            "end": ends[i],
            "progress": int(progresses[i])
        })
    
    tasks_db = new_tasks_db
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
