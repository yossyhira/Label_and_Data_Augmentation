import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from annotation_window import AnnotationWindow

class ModeSelectWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Mode")
        self.setGeometry(300, 300, 300, 200)

        layout = QVBoxLayout()

        self.annotation_button = QPushButton("Annotation")
        self.augmentation_button = QPushButton("Data Augmentation")

        layout.addWidget(self.annotation_button)
        layout.addWidget(self.augmentation_button)

        self.setLayout(layout)

        self.annotation_button.clicked.connect(self.open_annotation)

    def open_annotation(self):
        self.annotation_window = AnnotationWindow()
        self.annotation_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModeSelectWindow()
    window.show()
    sys.exit(app.exec_())
