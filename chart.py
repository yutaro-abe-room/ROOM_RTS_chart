import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

# ==========================================
# 1. ページ設定
# ==========================================
st.set_page_config(layout="wide", page_title="ROOM×RTS イベントプラン")

# ==========================================
# 2. データ管理 (Session State)
# ==========================================
if 'tasks' not in st.session_state:
    st.session_state.tasks = pd.DataFrame([
        {"id": 1, "assignee": "佐藤", "name": "企画立案", "start": datetime(2026, 3, 9), "end": datetime(2026, 3, 13), "progress": 100},
        {"id": 2, "assignee": "鈴木", "name": "会場選定・予約", "start": datetime(2026, 3, 11), "end": datetime(2026, 3, 18), "progress": 80},
        {"id": 3, "assignee": "田中", "name": "出演者オファー", "start": datetime(2026, 3, 13), "end": datetime(2026, 3, 23), "progress": 40},
        {"id": 4, "assignee": "高橋", "name": "広報・SNS運用", "start": datetime(2026, 3, 18), "end": datetime(2026, 4, 2), "progress": 10},
        {"id": 5, "assignee": "伊藤", "name": "当日運営マニュアル作成", "start": datetime(2026, 3, 28), "end": datetime(2026, 4, 5), "progress": 0},
    ])

if 'app_config' not in st.session_state:
    st.session_state.app_config = {
        "title": "ROOM×RTS イベントプラン",
        "subtitle": "プロジェクト進捗管理ダッシュボード"
    }

# ==========================================
# 3. タイトルエリア
# ==========================================
col1, col2 = st.columns([8, 2])
with col1:
    new_title = st.text_input("タイトル", value=st.session_state.app_config['title'], label_visibility="collapsed")
    st.session_state.app_config['title'] = new_title
    st.title(new_title)
    st.caption(st.session_state.app_config['subtitle'])

with col2:
    st.write("") # Spacer

# ==========================================
# 4. ガントチャート表示 (Altair使用)
# ==========================================
st.subheader("タイムライン (2026/03/09 〜 2026/07/31)")

df = st.session_state.tasks.copy()

# 日付型変換 (念のため)
df['start'] = pd.to_datetime(df['start'])
df['end'] = pd.to_datetime(df['end'])

# ガントチャート描画
if not df.empty:
    # 色分け用の計算
    def get_color(progress):
        if progress == 100: return "#2ecc71" # Green
        elif progress > 0: return "#3498db"  # Blue
        else: return "#f1c40f"               # Yellow

    df['color'] = df['progress'].apply(get_color)

    base = alt.Chart(df).encode(
        y=alt.Y('name', title='タスク名', sort=None),
        x=alt.X('start', title='日付', scale=alt.Scale(domain=[datetime(2026, 3, 9), datetime(2026, 7, 31)])),
        x2='end',
        color=alt.Color('color', scale=None, legend=None),
        tooltip=['assignee', 'name', 'start', 'end', 'progress']
    )

    chart = base.mark_bar(cornerRadius=5, height=20).properties(
        width='container', # 幅自動調整
        height=300
    )
    
    # テキストラベル (進捗%)
    text = base.mark_text(align='left', dx=5, color='black').encode(
        text=alt.Text('progress', format='d')
    )

    st.altair_chart(chart + text, use_container_width=True)
else:
    st.info("タスクがありません。下から追加してください。")

# ==========================================
# 5. タスク編集 (Data Editor)
# ==========================================
st.subheader("タスク編集")

edited_df = st.data_editor(
    st.session_state.tasks,
    num_rows="dynamic",
    column_config={
        "id": None, # IDは隠す
        "assignee": st.column_config.TextColumn("担当"),
        "name": st.column_config.TextColumn("タスク名", required=True),
        "start": st.column_config.DateColumn("開始日", required=True, format="YYYY-MM-DD"),
        "end": st.column_config.DateColumn("終了日", required=True, format="YYYY-MM-DD"),
        "progress": st.column_config.NumberColumn("進捗 (%)", min_value=0, max_value=100, step=10, format="%d%%"),
    },
    use_container_width=True,
    hide_index=True
)

# 変更があった場合のみ更新
if not edited_df.equals(st.session_state.tasks):
    # IDの自動採番 (新規行用)
    if len(edited_df) > len(st.session_state.tasks):
        max_id = st.session_state.tasks['id'].max() if not st.session_state.tasks.empty else 0
        # IDがNaN（新規追加行）の箇所を埋める
        edited_df['id'] = edited_df['id'].fillna(range(max_id + 1, max_id + 1 + len(edited_df)))

    st.session_state.tasks = edited_df
    st.rerun() # 画面リロードしてチャート反映
