import os
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QFileDialog
)
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt
from yolo_utils import save_yolo_label


class ImageLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.add_point(event.pos().x(), event.pos().y())


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

        # UI
        self.image_label = ImageLabel(self)

        self.select_button = QPushButton("Select Image Folder")
        self.save_button = QPushButton("Save")
        self.undo_button = QPushButton("Undo")
        self.toggle_button = QPushButton("Toggle Labels")
        self.next_button = QPushButton("Next")

        self.class_selector = QComboBox()
        self.load_classes()

        self.select_button.clicked.connect(self.select_folder)
        self.save_button.clicked.connect(self.save_and_next)
        self.undo_button.clicked.connect(self.undo)
        self.toggle_button.clicked.connect(self.toggle_labels)
        self.next_button.clicked.connect(self.next_image)

        layout = QVBoxLayout()
        layout.addWidget(self.select_button)
        layout.addWidget(self.image_label)
        layout.addWidget(self.class_selector)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.undo_button)
        btn_layout.addWidget(self.toggle_button)
        btn_layout.addWidget(self.next_button)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # --------------------------
    # フォルダ選択
    # --------------------------
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.image_folder = folder
            self.image_paths = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith((".jpg", ".png", ".jpeg"))
            ]
            self.current_index = 0
            self.load_image()

    # --------------------------
    # 画像読み込み
    # --------------------------
    def load_image(self):
        if not self.image_paths:
            return

        if self.current_index >= len(self.image_paths):
            return

        self.pixmap = QPixmap(self.image_paths[self.current_index])
        self.image_label.setPixmap(self.pixmap)
        self.boxes.clear()
        self.points.clear()
        self.update()

    # --------------------------
    # クリック処理
    # --------------------------
    def add_point(self, x, y):
        self.points.append((x, y))
        if len(self.points) == 4:
            xs = [p[0] for p in self.points]
            ys = [p[1] for p in self.points]

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            self.boxes.append((x_min, y_min, x_max, y_max))
            self.points.clear()
            self.update()

    # --------------------------
    # 描画
    # --------------------------
    def paintEvent(self, event):
        super().paintEvent(event)

        if not hasattr(self, "pixmap"):
            return

        painter = QPainter(self.image_label)
        if self.show_labels:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            for box in self.boxes:
                x_min, y_min, x_max, y_max = box
                painter.drawRect(x_min, y_min,
                                 x_max - x_min, y_max - y_min)

    # --------------------------
    # Undo
    # --------------------------
    def undo(self):
        if self.boxes:
            self.boxes.pop()
            self.update()

    # --------------------------
    # Toggle表示
    # --------------------------
    def toggle_labels(self):
        self.show_labels = not self.show_labels
        self.update()

    # --------------------------
    # 次画像
    # --------------------------
    def next_image(self):
        self.current_index += 1
        self.load_image()

    # --------------------------
    # 保存
    # --------------------------
    def save_and_next(self):
        if not self.image_paths:
            return

        img_path = self.image_paths[self.current_index]
        class_id = self.class_selector.currentIndex()

        save_yolo_label(
            img_path,
            self.boxes,
            class_id,
            self.pixmap.width(),
            self.pixmap.height()
        )

        self.next_image()

    # --------------------------
    # クラス読み込み
    # --------------------------
    def load_classes(self):
        if os.path.exists("classes.txt"):
            with open("classes.txt", "r") as f:
                for line in f:
                    self.class_selector.addItem(line.strip())
        else:
            self.class_selector.addItem("object")
            with open("classes.txt", "w") as f:
                f.write("object\n")

    # --------------------------
    # Ctrl+Z
    # --------------------------
    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z:
            self.undo()
