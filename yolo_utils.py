import os

def save_yolo_label(label_path, boxes, class_id, img_width, img_height):
    """
    YOLO形式で保存
    class x_center y_center width height (0~1正規化)
    """

    with open(label_path, "w") as f:
        for box in boxes:
            x_min, y_min, x_max, y_max = box

            x_center = ((x_min + x_max) / 2) / img_width
            y_center = ((y_min + y_max) / 2) / img_height
            width = (x_max - x_min) / img_width
            height = (y_max - y_min) / img_height

            line = f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n"
            f.write(line)
