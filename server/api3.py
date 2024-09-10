import os
import streamlit as st

from src.Config import Config
from src.Web import Web

# Drive読み取りで必要か？
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/app/private/sync-frame-runner.json"
web = Web(Config("private/syncframe.json"))

key = st.query_params["key"] if "key" in st.query_params else None
worksheet = st.query_params["worksheet"] if "worksheet" in st.query_params else None

items = []
if key and worksheet:
    items = web.prepare(key).get_sheet(worksheet)
if len(items) == 0:
    st.write("キーとワークシートが不明です")
else:
    st.markdown(f"""
        - **キー**: {key}
        - **ワークシート**: {worksheet}
        - **使用量/限界**: {web.get_frame_used()} / {web.get_frame_limit()}
    """)
    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 3, 1, 1, 1])
    with col1:
        st.write("**ID**")
    with col2:
        st.write("**メモ**")
    with col3:
        st.write("**URL**")
    with col4:
        st.write("**プレビュー**")
    with col5:
        st.write("**更新**")
    with col6:
        st.write("**削除**")

    for i, item in enumerate(items):
        st.markdown("<hr>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 3, 1, 1, 1])
        with col1:
            st.write(item.id)
        with col2:
            st.write(item.title)
        with col3:
            st.write(item.url)
        with col4:
            st.image(item.public_url, use_column_width=True)
        with col5:
            if st.button(f"更新", key=2*i+0):
                web.prepare(key).upload_object(worksheet, item.id)
                st.write(f"{item.id}を更新")
        with col6:
            if st.button(f"削除", key=2*i+1):
                web.prepare(key).delete_object(worksheet, item.id)
                st.write(f"{item.id}を削除")    
