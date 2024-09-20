import os
import streamlit as st
from PIL import Image

from src.Config import Config
from src.Web import Web

web = Web(Config("private/syncframe.json"))

key = st.query_params["key"] if "key" in st.query_params else None
worksheet = st.query_params["worksheet"] if "worksheet" in st.query_params else None

st.markdown(
    """
    <style>
    .stAppDeployButton {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)

items = []
if key and worksheet:
    items = web.prepare(key).get_sheet(worksheet)
if len(items) == 0:
    st.write("ワークシート内に画像が見つかりません")
else:
    st.markdown(f"""
        - **キー**: {key}
        - **ワークシート**: {worksheet}
        - **画像使用量/限界**: {web.get_frame_used()} / {web.get_frame_limit()}
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
            if item.url:
                st.write(item.url)
            else:
                uploaded_file = st.file_uploader("直接アップロード", type=["jpg", "png"])
                if uploaded_file is not None:
                    im = Image.open(uploaded_file)
                    web.prepare(key).upload_object(worksheet, item.id, im)
                    st.image(im, caption='アップロードされた画像', use_column_width=True)
        with col4:
            st.image(item.public_url, use_column_width=True)
        with col5:
            if item.url:
                if st.button(f"更新", key=2*i+0):
                    try:
                        web.prepare(key).upload_object(worksheet, item.id)
                        st.write(f"{item.id}を更新")
                    except Exception as ex:
                        st.write("エラー: " + str(ex))
            else:
                st.button("更新", disabled=True)
        with col6:
            if st.button(f"削除", key=2*i+1):
                try:
                    web.prepare(key).delete_object(worksheet, item.id)
                    st.write(f"{item.id}を削除")    
                except Exception as ex:
                    st.write("エラー: " + str(ex))

# streamlit run web.py --server.port 8080
