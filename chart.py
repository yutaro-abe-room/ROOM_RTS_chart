import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timedelta

# ページ設定
st.set_page_config(layout="wide", page_title="ROOM×RTS イベントプラン")

# ==========================================
# データ管理 (Session State)
# ==========================================
if 'tasks' not in st.session_state:
    # 初期データ
    initial_data = [
        {"id": 1, "assignee": "佐藤", "name": "企画立案", "start": "2026-03-09", "end": "2026-03-13", "progress": 100},
        {"id": 2, "assignee": "鈴木", "name": "会場選定・予約", "start": "2026-03-11", "end": "2026-03-18", "progress": 80},
        {"id": 3, "assignee": "田中", "name": "出演者オファー", "start": "2026-03-13", "end": "2026-03-23", "progress": 40},
        {"id": 4, "assignee": "高橋", "name": "広報・SNS運用", "start": "2026-03-18", "end": "2026-04-02", "progress": 10},
        {"id": 5, "assignee": "伊藤", "name": "当日運営マニュアル作成", "start": "2026-03-28", "end": "2026-04-05", "progress": 0},
    ]
    # DataFrameに変換し、日付列をdatetime型にする（ここが重要！）
    df_init = pd.DataFrame(initial_data)
    df_init['start'] = pd.to_datetime(df_init['start'])
    df_init['end'] = pd.to_datetime(df_init['end'])
    st.session_state.tasks = df_init

if 'app_config' not in st.session_state:
    st.session_state.app_config = {
        "title": "ROOM×RTS イベントプラン",
        "subtitle": "プロジェクト進捗管理ダッシュボード"
    }

# ==========================================
# ロジック (日付計算など)
# ==========================================
def process_tasks_for_gantt(df):
    base_start_date = datetime(2026, 3, 9)
    base_end_date = datetime(2026, 7, 31)
    
    # DataFrameを辞書のリストに変換して処理
    tasks_data = df.to_dict('records')
    
    processed = []
    for t in tasks_data:
        task = t.copy()
        try:
            # datetime型の場合はそのまま使用、文字列なら変換
            if isinstance(task['start'], str):
                task['start_dt'] = datetime.strptime(task['start'], '%Y-%m-%d')
            else:
                task['start_dt'] = task['start']
                
            if isinstance(task['end'], str):
                task['end_dt'] = datetime.strptime(task['end'], '%Y-%m-%d')
            else:
                task['end_dt'] = task['end']
                
            processed.append(task)
        except ValueError:
            continue

    total_days = (base_end_date - base_start_date).days + 1
    date_range = [base_start_date + timedelta(days=x) for x in range(total_days)]

    for task in processed:
        start_offset = (task['start_dt'] - base_start_date).days
        duration = (task['end_dt'] - task['start_dt']).days + 1
        
        if start_offset + duration < 0:
            task['visible'] = False
        else:
            if start_offset < 0:
                visible_duration = duration + start_offset
                task['offset_percent'] = 0
                task['width_percent'] = (visible_duration / total_days) * 100
            else:
                task['offset_percent'] = (start_offset / total_days) * 100
                task['width_percent'] = (duration / total_days) * 100
            task['visible'] = True

        p = int(task['progress'])
        if p == 100: task['status_class'] = 'status-done'
        elif p > 0:  task['status_class'] = 'status-wip'
        else:        task['status_class'] = 'status-todo'

    return processed, date_range, total_days

# データ処理実行
tasks, date_range, total_days = process_tasks_for_gantt(st.session_state.tasks)

# ==========================================
# HTML生成
# ==========================================

# 日付ヘッダーHTML
days_html = ""
grid_lines_html = ""
for i, day in enumerate(date_range):
    weekday = day.weekday()
    day_class = ""
    if weekday == 5: day_class = "sat"
    elif weekday == 6: day_class = "sun"
    elif weekday == 0: day_class = "mon"
    
    day_str = day.strftime('%d')
    date_str = day.strftime('%m/%d')
    
    days_html += f'''
        <div class="day-marker {day_class}">
            {day_str}<br>
            <span style="font-size:0.6rem;">{date_str}</span>
        </div>
    '''
    
    left_percent = i * (100 / total_days)
    grid_lines_html += f'<div class="grid-line {day_class}" style="left: {left_percent}%;"></div>'

# タスク行HTML
tasks_html = ""
for task in tasks:
    bar_html = ""
    if task.get('visible'):
        bar_html = f'''
        <div class="gantt-bar {task['status_class']}" 
             style="left: {task['offset_percent']}%; width: {task['width_percent']}%;"
             title="{task['name']} ({task['assignee']}): {task['progress']}%">
            <span>{task['progress']}%</span>
        </div>
        '''
    
    tasks_html += f'''
    <div class="task-row">
        <div class="sticky-col-data">
            <div class="assignee-cell" title="{task['assignee']}">{task['assignee']}</div>
            <div class="task-name" title="{task['name']}">{task['name']}</div>
        </div>
        <div class="chart-area">
            {grid_lines_html}
            {bar_html}
        </div>
    </div>
    '''

# 全体HTML
full_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <style>
        /* --- ベースデザイン (ライトモード) --- */
        :root {{
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
            --sat-color: #eaf4ff;
            --sun-color: #ffeaea;
            --mon-border: #bdc3c7;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 0; /* Streamlitのコンテナ内に収めるため余白調整 */
        }}
        .header-container {{ margin-bottom: 30px; }}
        h1 {{
            text-align: left; font-size: 2rem; font-weight: 800; color: #2c3e50; margin: 0;
            letter-spacing: -0.5px; border-bottom: 2px solid transparent;
        }}
        .subtitle {{ text-align: left; color: var(--text-sub); margin-top: 5px; font-weight: 500; }}
        h2 {{
            font-size: 1.2rem; margin-bottom: 15px; color: #34495e;
            border-left: 4px solid var(--accent-color); padding-left: 10px;
        }}
        .card {{
            background-color: var(--panel-color); border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); padding: 20px; margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }}
        .gantt-scroll-wrapper {{
            overflow-x: auto; border: 1px solid var(--border-color);
            border-radius: 8px; position: relative; min-width: 100%;
        }}
        .timeline-header {{
            display: flex; background-color: #f8fafc; border-bottom: 1px solid var(--border-color);
            min-width: {total_days * 35 + 300}px; position: sticky; top: 0; z-index: 20;
        }}
        .sticky-col-header {{
            position: sticky; left: 0; z-index: 30; display: flex;
            background-color: #f8fafc; box-shadow: 2px 0 5px rgba(0,0,0,0.05);
        }}
        .assignee-header {{ width: 80px; padding: 12px 10px; font-weight: 600; color: #555; border-right: 1px solid var(--border-color); text-align: center; flex-shrink: 0; }}
        .task-name-header {{ width: 220px; padding: 12px 15px; font-weight: 600; color: #555; border-right: 1px solid var(--border-color); flex-shrink: 0; }}
        .timeline-days {{ flex-grow: 1; display: flex; }}
        .day-marker {{
            flex: 1; text-align: center; font-size: 0.75rem; padding: 8px 0;
            border-left: 1px solid var(--border-color); color: var(--text-sub);
            min-width: 35px; box-sizing: border-box;
        }}
        .day-marker.sat {{ background-color: var(--sat-color); color: #3498db; }}
        .day-marker.sun {{ background-color: var(--sun-color); color: #e74c3c; }}
        .day-marker.mon {{ border-left: 2px solid var(--mon-border); }}
        .task-row {{
            display: flex; border-bottom: 1px solid var(--border-color); height: 44px;
            align-items: center; min-width: {total_days * 35 + 300}px; position: relative;
        }}
        .task-row:hover {{ background-color: #f8f9fa; }}
        .sticky-col-data {{
            position: sticky; left: 0; z-index: 10; display: flex;
            background-color: var(--panel-color); box-shadow: 2px 0 5px rgba(0,0,0,0.05);
            height: 100%; align-items: center;
        }}
        .assignee-cell {{
            width: 80px; padding: 0 10px; font-size: 0.85rem; text-align: center;
            border-right: 1px solid var(--border-color); white-space: nowrap;
            overflow: hidden; text-overflow: ellipsis; color: #555; background-color: #fdfdfd; flex-shrink: 0;
        }}
        .task-name {{
            width: 220px; padding: 0 15px; font-size: 0.9rem; white-space: nowrap;
            overflow: hidden; text-overflow: ellipsis; border-right: 1px solid var(--border-color);
            font-weight: 500; flex-shrink: 0;
        }}
        .chart-area {{ flex-grow: 1; position: relative; height: 100%; }}
        .grid-line {{
            position: absolute; top: 0; bottom: 0; width: 1px; background-color: #f1f5f9;
            z-index: 0; border-left: 1px solid var(--border-color); box-sizing: border-box;
        }}
        .grid-line.sat {{ background-color: var(--sat-color); }}
        .grid-line.sun {{ background-color: var(--sun-color); }}
        .grid-line.mon {{ border-left: 2px solid var(--mon-border); }}
        .gantt-bar {{
            position: absolute; top: 10px; height: 24px; border-radius: 4px; z-index: 5;
            display: flex; align-items: center; justify-content: center; font-size: 0.75rem;
            color: #fff; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s; cursor: pointer;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 5px;
        }}
        .gantt-bar:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); z-index: 100; overflow: visible; }}
        .status-done {{ background-color: var(--color-done); }}
        .status-wip {{ background-color: var(--color-wip); }}
        .status-todo {{ background-color: var(--color-todo); color: #555; }}
    </style>
</head>
<body>
    <div class="header-container">
        <h1>{st.session_state.app_config['title']}</h1>
        <div class="subtitle">{st.session_state.app_config['subtitle']}</div>
    </div>

    <div class="card">
        <h2>タイムライン (2026/03/09 〜 2026/07/31)</h2>
        <div class="gantt-scroll-wrapper">
            <div class="timeline-header">
                <div class="sticky-col-header">
                    <div class="assignee-header">担当</div>
                    <div class="task-name-header">タスク名</div>
                </div>
                <div class="timeline-days">
                    {days_html}
                </div>
            </div>
            {tasks_html}
        </div>
    </div>
</body>
</html>
"""

# HTML埋め込み
components.html(full_html, height=600, scrolling=True)

# ==========================================
# 編集機能
# ==========================================
st.markdown("---")
st.subheader("📝 タスク編集")

# データエディタ設定
edited_df = st.data_editor(
    st.session_state.tasks,
    num_rows="dynamic",
    column_config={
        "id": None, # IDは非表示
        "assignee": st.column_config.TextColumn("担当"),
        "name": st.column_config.TextColumn("タスク名", required=True),
        "start": st.column_config.DateColumn("開始日", required=True, format="YYYY-MM-DD"),
        "end": st.column_config.DateColumn("終了日", required=True, format="YYYY-MM-DD"),
        "progress": st.column_config.NumberColumn("進捗 (%)", min_value=0, max_value=100, step=10, format="%d%%"),
    },
    use_container_width=True,
    hide_index=True
)

# 変更検知と更新
if not edited_df.equals(st.session_state.tasks):
    # 新規行のID補完
    if len(edited_df) > len(st.session_state.tasks):
        max_id = st.session_state.tasks['id'].max() if not st.session_state.tasks.empty else 0
        edited_df['id'] = edited_df['id'].fillna(range(max_id + 1, max_id + 1 + len(edited_df)))
    
    st.session_state.tasks = edited_df
    st.rerun()
