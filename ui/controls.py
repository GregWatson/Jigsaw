
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

class ControlPanel(QWidget):
    def __init__(self, graphics_area, parent=None):
        super().__init__(parent)
        self.graphics_area = graphics_area
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        
        title = QLabel("Controls")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #ddd;")
        layout.addWidget(title)
        
        self.btn_add_rect = QPushButton("Add Shape")
        self.btn_add_rect.clicked.connect(self.graphics_area.add_rect)
        layout.addWidget(self.btn_add_rect)
        
        self.btn_add_img = QPushButton("Add Image")
        self.btn_add_img.clicked.connect(self.graphics_area.add_image_placeholder)
        layout.addWidget(self.btn_add_img)
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.graphics_area.clear_scene)
        self.btn_clear.setStyleSheet("background-color: #552222;") # Reddish for delete
        layout.addWidget(self.btn_clear)

        self.btn_fix_parallax = QPushButton("Fix parallax")
        # Connection will be handled by MainWindow to coordinate with popup flow
        self.btn_fix_parallax.setVisible(False)
        layout.addWidget(self.btn_fix_parallax)
        
        # Expand filler to push items up
        layout.addStretch()
