import os
import streamlit as st
from PIL import Image

from src.Config import Config
from src.Web import Web

web = Web(Config("private/syncframe.json"))

key = st.query_params["key"] if "key" in st.query_params else None
worksheet = st.query_params["worksheet"] if "worksheet" in st.query_params else None

st.set_page_config(layout="wide")
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
if key is None or worksheet is None:
    st.write("ワークシート情報が取得できません")
else:
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

        col1, col2, col3, col4, col5 = st.columns([1, 2, 3, 4, 1])
        with col1:
            st.write("**ID**")
        with col2:
            st.write("**メモ**")
        with col3:
            st.write("**URL**")
        with col4:
            st.write("**操作**")
        with col5:
            st.write("**プレビュー**")

        for i, item in enumerate(items):
            st.markdown("<hr>", unsafe_allow_html=True)
            col1, col2, col3, col4, col5 = st.columns([1, 2, 3, 4, 1])
            image_url_or_obj = item.public_url
            with col1:
                st.write(item.id)
            with col2:
                st.write(item.title)
            with col3:
                st.write(item.url)
            with col4:
                if item.has_external_image():
                    if st.button(f"更新", key=2*i+0):
                        try:
                            web.prepare(key).upload_object(worksheet, item.id)
                            st.write(f"{item.id}を更新")
                            st.cache_resource.clear()
                        except Exception as ex:
                            st.write("エラー: " + str(ex))
                if item.url is None or item.has_direct_image():
                    uploaded_file = st.file_uploader("直接アップロード", type=["jpg", "png"])
                    if uploaded_file is not None:
                        im = Image.open(uploaded_file)
                        im.filename = uploaded_file.name
                        web.prepare(key).upload_object(worksheet, item.id, im)
                        image_url_or_obj = im

                if st.button(f"削除", key=2*i+1):
                    try:
                        web.prepare(key).delete_object(worksheet, item.id)
                        st.write(f"{item.id}を削除")    
                    except Exception as ex:
                        st.write("エラー: " + str(ex))
            with col5:
                st.image(image_url_or_obj, use_column_width=True)

# streamlit run web.py --server.port 8080
