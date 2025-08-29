from nicegui import tailwind, app, ui
import webview
import os
from PIL import Image
import math

MAX_COLUMN_AMOUNT = 35  # 单行图片数量限制

img_width = 0
img_height = 0
picked_image_paths = []
picked_image_name = "Spritesheet"
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")


# ------ 事件处理函数 ------


def get_new_filename(filename: str) -> str:
    # 获取文件名及扩展名
    basename = os.path.basename(filename)
    # 分离文件名及扩展名
    name, ext = os.path.splitext(basename)
    # 返回 _ 前面的字符
    return name.split("_")[0]


async def choose_images():
    file_types = ("Image Files (*.png;*.jpg)", "All files (*.*)")  # 必须是这个格式
    files = await app.native.main_window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True, file_types=file_types)  # type: ignore
    if files:
        try:
            first_images = Image.open(files[0])
            global img_width, img_height, picked_image_paths, picked_image_name
            img_width, img_height = first_images.size
            picked_image_paths = [f for f in files]
            picked_image_name = get_new_filename(files[0])
            input_images_status.set_value(
                f"选中 {len(files)} 张图片, 尺寸 {img_width}x{img_height} (px)"
            )
        except Exception as e:
            ui.notify(f"打开图片失败：{e}")


async def choose_output_dir():
    dir = await app.native.main_window.create_file_dialog(webview.FileDialog.FOLDER)  # type: ignore
    if dir:
        input_output_dir.set_value(dir[0])  # 注意：返回值 dir 是元组


def on_btn_generate_clicked():
    picked_count = len(picked_image_paths)
    if picked_count < 2:
        ui.notify("请选择至少两张以上图片", timeout=500)
        return

    column = int(
        picked_count if picked_count < input_column.value else input_column.value
    )
    row = math.ceil(picked_count / column)
    sprite_width = img_width * column
    sprite_height = img_height * row

    # 创建空白图集
    spritesheet = Image.new("RGBA", (sprite_width, sprite_height))
    # 逐个粘贴图片
    x_offset, y_offset = 0, 0
    for index, path in enumerate(picked_image_paths):
        with Image.open(path) as img:
            spritesheet.paste(img, (x_offset, y_offset))
            x_offset += img_width
            if (index + 1) % column == 0:
                x_offset = 0
                y_offset += img_height

    # 保存图集
    try:
        output_path = input_output_dir.value or desktop_path
        save_path = os.path.join(output_path, f"{picked_image_name}.png")
        spritesheet.save(save_path)
        # 判断是否成功保存(文件存在则成功)
        if os.path.exists(save_path):
            ui.notify("生成图片成功", type="positive", timeout=500)
        else:
            ui.notify("生成图片失败：文件未保存", timeout=500)
    except Exception as e:
        ui.notify(f"生成图片失败：{e}")


# ------ 界面布局 ------

with ui.column().classes("w-full font-mono"):
    # 选取打包图片输入框
    with ui.row().classes("w-full"):
        with ui.input(label="选择图片", value="选中 0 张图片, 尺寸 0x0 (px)").props(
            "outlined readonly"
        ).classes("grow") as input_images_status:
            ui.button(icon="add_photo_alternate", on_click=choose_images).props("flat")

    # 导出目录输入框
    with ui.row().classes("w-full"):
        with ui.input(label="导出目录", value=desktop_path).props(
            "outlined readonly"
        ).classes("grow") as input_output_dir:
            ui.button(icon="folder_open", on_click=choose_output_dir).props("flat")

    # 单行图片数量限制输入框
    input_column = (
        ui.number(
            label=f"最大单行图片数量 (Max: {MAX_COLUMN_AMOUNT})",
            value=6,
            min=2,
            max=MAX_COLUMN_AMOUNT,
            precision=0,  # 输入框小数位数
            format="%.0f",  # 显示小数点后多少位
        )
        .props("outlined")
        .classes("w-full")
    )

    # 生成按钮
    ui.button("Generate Spritesheet", on_click=on_btn_generate_clicked).props(
        "no-caps"
    ).classes("w-full")

    # 版本信息
    ui.label("Version 1.0.0, © 2025 KeniGht").classes(
        "w-full text-center text-gray-400"
    ).style("font-size: 10px; margin-top: -0.5rem; margin-bottom: -0.5rem;")


# ------ App 设置 ------

# Set window properties
app.native.window_args["resizable"] = False
app.native.window_args["maximized"] = False

# Run the app with native window
# 打包后加上 reload=False 否则关闭软件后不会关闭 web server
ui.run(native=True, reload=False, window_size=(420, 355), title="Spritesheet Maker")
