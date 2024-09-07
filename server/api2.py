import os, sys, subprocess, traceback, json
from fastapi import FastAPI
import gradio as gr

from src.Config import Config
from src.Web import Web


# Drive読み取りで必要か？
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/app/private/sync-frame-runner.json"

app = FastAPI()
web = Web(Config("private/syncframe.json"))


@app.get('/sheet/{key}/{worksheet}.json')
def get_sheet_json(key, worksheet):
    try:
        return web.prepare(key).get_sheet_json(worksheet)
    except Exception as ex:
        print("ERROR", ex, traceback.format_exc())
        return json.dumps({"status": "FAIL", "reason": str(ex)})


@app.get('/delete/{key}/{worksheet}')
def delete_work_objects(key, worksheet):
    try:
        web.prepare(key).delete_work_objects(worksheet)
        return "OK"
    except Exception as ex:
        return "FAIL\n" + ex.__class__.__name__ + "\n" + str(ex), 404

@app.get('/delete/{key}/{worksheet}/{id}')
def delete_object(key, worksheet, id):
    try:
        web.prepare(key).delete_object(worksheet, id)
        return "OK"
    except Exception as ex:
        return "FAIL\n" + ex.__class__.__name__ + "\n" + str(ex), 404

@app.get('/upload/{key}/{worksheet}/{id}')
def upload_object(key, worksheet, id):
    try:
        web.prepare(key).upload_object(worksheet, id)
        return "OK"
    except Exception as ex:
        return "FAIL\n" + ex.__class__.__name__ + "\n" + str(ex), 404

##### Gradio #####
def gr_get_session(key, worksheet, request: gr.Request):
    if request:
        key = request.query_params.get("key")
        worksheet = request.query_params.get("worksheet")
    return key, worksheet

def gr_update_image(key, worksheet, id):
    web.prepare(key).upload_object(worksheet, id)
    return gr.Image(label="フレーム", value=web.get_public_url(worksheet, id), height=96, show_download_button=False)

def gr_delete_image(key, worksheet, id):
    web.prepare(key).delete_object(worksheet, id)
    return gr.Image(label="フレーム", height=96, show_download_button=False)

css = """
.row-bg0 {
    background-color: #FFFFFF;
}
.row-bg1 {
    background-color: #DDDDDD;
}
"""

with gr.Blocks(css=css) as g:
    st_key = gr.State()
    st_worksheet = gr.State()
    btn_load = gr.Button("読み込み")
    btn_load.click(fn=gr_get_session, inputs=[st_key, st_worksheet], outputs=[st_key, st_worksheet])

    @gr.render(inputs=[st_key, st_worksheet], triggers=[st_key.change])
    def show_table(key, worksheet):
        if key is None or worksheet is None:
            gr.Markdown("スプレッドシートを読み込みます！")
        else:
            items = web.prepare(key).get_sheet(worksheet)
            gr.Markdown(
                f"""
                - キー: {key}
                - ワークシート: {worksheet}
                - 使用量 / 限界: {web.get_frame_used()} / {web.get_frame_limit()}
            """)
            for i, item in enumerate(items):
                c = "row-bg0" if i % 2 == 0 else "row-bg1"
                with gr.Row(elem_classes=c):
                    label_id = gr.Label(label="ID", value=item.id)
                    label_title = gr.Label(label="Title", value=item.title)
                    img_src = gr.Image(label=item.url, value=item.url, height=96, show_download_button=False)
                    img_dst = gr.Image(label="表示先", value=item.public_url, height=96, show_download_button=False)
                    btn_update = gr.Button("更新")
                    btn_delete = gr.Button("削除")
                    btn_update.click(fn=gr_update_image, inputs=[st_key, st_worksheet, label_id], outputs=[img_dst])
                    btn_delete.click(fn=gr_delete_image, inputs=[st_key, st_worksheet, label_id], outputs=[img_dst])

app = gr.mount_gradio_app(app, g, path="/")