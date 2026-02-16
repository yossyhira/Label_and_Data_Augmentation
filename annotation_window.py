import os
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QFileDialog
)
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt
from yolo_utils import save_yolo_label


# =========================================
# 画像表示ラベル（クリック座標補正付き）
# =========================================
class ImageLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.setAlignment(Qt.AlignCenter)

    def mousePressEvent(self, event):
        if not hasattr(self.parent_window, "original_pixmap"):
            return

        pixmap = self.parent_window.original_pixmap

        label_width = self.width()
        label_height = self.height()

        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        offset_x = (label_width - pixmap_width) // 2
        offset_y = (label_height - pixmap_height) // 2

        x = event.pos().x() - offset_x
        y = event.pos().y() - offset_y

        if 0 <= x <= pixmap_width and 0 <= y <= pixmap_height:
            self.parent_window.add_point(x, y)


# =========================================
# アノテーションウィンドウ
# =========================================
class AnnotationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Annotation Tool")
        self.setGeometry(200, 200, 1000, 800)

        self.points = []
        self.boxes = []
        self.show_labels = True

        self.current_index = 0
        self.image_paths = []
        self.image_folder = ""
        self.label_folder = ""

        # UI
        self.image_label = ImageLabel(self)

        self.select_img_button = QPushButton("Select Image Folder")
        self.select_label_button = QPushButton("Select Label Folder")

        self.save_button = QPushButton("Save")
        self.undo_button = QPushButton("Undo")
        self.toggle_button = QPushButton("Toggle Labels")
        self.prev_button = QPushButton("Prev")
        self.next_button = QPushButton("Next")

        self.class_selector = QComboBox()
        self.load_classes()

        # connect
        self.select_img_button.clicked.connect(self.select_image_folder)
        self.select_label_button.clicked.connect(self.select_label_folder)
        self.save_button.clicked.connect(self.save_and_next)
        self.undo_button.clicked.connect(self.undo)
        self.toggle_button.clicked.connect(self.toggle_labels)
        self.prev_button.clicked.connect(self.prev_image)
        self.next_button.clicked.connect(self.next_image)

        # layout
        layout = QVBoxLayout()
        layout.addWidget(self.select_img_button)
        layout.addWidget(self.select_label_button)
        layout.addWidget(self.image_label)
        layout.addWidget(self.class_selector)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.undo_button)
        btn_layout.addWidget(self.toggle_button)
        btn_layout.addWidget(self.prev_button)
        btn_layout.addWidget(self.next_button)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # =========================================
    # フォルダ選択
    # =========================================
    def select_image_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.image_folder = folder
            self.image_paths = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith((".jpg", ".png", ".jpeg"))
            ]
            self.image_paths.sort()
            self.current_index = 0
            self.load_image()

    def select_label_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Label Folder")
        if folder:
            self.label_folder = folder

    # =========================================
    # 画像読み込み
    # =========================================
    def load_image(self):
        if not self.image_paths:
            return

        if self.current_index < 0 or self.current_index >= len(self.image_paths):
            return

        self.original_pixmap = QPixmap(self.image_paths[self.current_index])
        self.points.clear()
        self.boxes.clear()
        self.update_display()

    # =========================================
    # クリック処理（4点方式）
    # =========================================
    def add_point(self, x, y):
        self.points.append((x, y))

        if len(self.points) == 4:
            xs = [p[0] for p in self.points]
            ys = [p[1] for p in self.points]

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            self.boxes.append((x_min, y_min, x_max, y_max))
            self.points.clear()

        self.update_display()

    # =========================================
    # 描画更新
    # =========================================
    def update_display(self):
        if not hasattr(self, "original_pixmap"):
            return

        pixmap = self.original_pixmap.copy()
        painter = QPainter(pixmap)

        # ボックス描画
        if self.show_labels:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            for box in self.boxes:
                x_min, y_min, x_max, y_max = box
                painter.drawRect(
                    int(x_min),
                    int(y_min),
                    int(x_max - x_min),
                    int(y_max - y_min)
                )

        # 点描画
        point_pen = QPen(Qt.blue, 6)
        painter.setPen(point_pen)
        for point in self.points:
            painter.drawPoint(int(point[0]), int(point[1]))

        painter.end()

        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()

    # =========================================
    # Undo
    # =========================================
    def undo(self):
        if self.boxes:
            self.boxes.pop()
        self.update_display()

    # =========================================
    # Toggle表示
    # =========================================
    def toggle_labels(self):
        self.show_labels = not self.show_labels
        self.update_display()

    # =========================================
    # 次画像
    # =========================================
    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_image()

    # =========================================
    # 前画像
    # =========================================
    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()

    # =========================================
    # 保存（YOLO形式）
    # =========================================
    def save_and_next(self):
        if not self.image_paths or not self.label_folder:
            return

        img_path = self.image_paths[self.current_index]
        filename = os.path.splitext(os.path.basename(img_path))[0]
        label_path = os.path.join(self.label_folder, filename + ".txt")

        class_id = self.class_selector.currentIndex()

        save_yolo_label(
            label_path,
            self.boxes,
            class_id,
            self.original_pixmap.width(),
            self.original_pixmap.height()
        )

        self.next_image()

    # =========================================
    # クラス読み込み
    # =========================================
    def load_classes(self):
        if os.path.exists("classes.txt"):
            with open("classes.txt", "r") as f:
                for line in f:
                    self.class_selector.addItem(line.strip())
        else:
            self.class_selector.addItem("object")
            with open("classes.txt", "w") as f:
                f.write("object\n")

    # =========================================
    # Ctrl+Z
    # =========================================
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z:
            self.undo()
