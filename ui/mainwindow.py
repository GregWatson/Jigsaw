
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QMenu, QFileDialog, QDialog, QPushButton
from PySide6.QtGui import QAction, QColor, QPalette, QPixmap, QImage
import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from .graphics_area import GraphicsArea
from .controls import ControlPanel
from .parallax_worker import ParallaxHelpDialog, apply_parallax_correction

class ImageLabel(QLabel):
    clicked = Signal(QPixmap)

    def __init__(self, text):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #333; border: 1px dashed #555; color: #888; font-size: 16px;")
        self._original_pixmap = None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        load_action = QAction("Load image", self)
        load_action.triggered.connect(self.load_image)
        menu.addAction(load_action)
        menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._original_pixmap:
            self.clicked.emit(self._original_pixmap)
        super().mousePressEvent(event)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.jpg *.jpeg)")
        if file_name:
            self.set_image(file_name)

    def set_image(self, file_path):
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            self._original_pixmap = pixmap
            self.update_display()
            self.setStyleSheet("background-color: #333; border: none;")

    def resizeEvent(self, event):
        if self._original_pixmap:
            self.update_display()
        super().resizeEvent(event)

    def update_display(self):
        if not self._original_pixmap:
            return
        # Scale to current size, keep aspect ratio
        scaled = self._original_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jigsaw - Windows 11 Graphic App")
        self.resize(2000, 1700)
        
        # Setup Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout (Horizontal: Controls | Content)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Components
        self.work_image = GraphicsArea()
        self.controls = ControlPanel(self.work_image)
        self.controls.btn_fix_parallax.clicked.connect(self.start_parallax_flow)
        
        self.current_source_label = None
        
        # --- Right Side Content Area (Vertical: Top Images | Bottom Graphics) ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top Row (3 Images)
        top_row_widget = QWidget()
        top_row_widget.setMaximumHeight(250) # Keep images fairly small
        top_row_layout = QHBoxLayout(top_row_widget)
        top_row_layout.setContentsMargins(10, 10, 10, 10)
        top_row_layout.setSpacing(10)
        
        labels = ["Box cover", "So far", "Pieces"]
        self.image_labels = {}
        for text in labels:
            label = ImageLabel(text)
            label.clicked.connect(lambda p, s=text: self.set_active_image(p, s))
            self.image_labels[text] = label
            top_row_layout.addWidget(label)
            
        content_layout.addWidget(top_row_widget, 0) # 0 stretch factor (fixed size/no growth)
        content_layout.addWidget(self.work_image, 1) # 1 stretch factor (takes all remaining space)
        
        # Add to main layout
        main_layout.addWidget(self.controls, 1)      # Controls take small width
        main_layout.addWidget(content_widget, 4)     # Content takes more width
        
        # Styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #222;
            }
            QWidget {
                color: #eee;
            }
            QPushButton {
                background-color: #444;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        self.setup_menu()

    def load_box_cover(self, file_path):
        if "Box cover" in self.image_labels:
            self.image_labels["Box cover"].set_image(file_path)
            # Optionally simulate a click to make it active immediately
            # self.set_active_image(self.image_labels["Box cover"]._original_pixmap, "Box cover")

        
    def set_active_image(self, pixmap, source_label):
        self.current_source_label = source_label
        self.current_pixmap = pixmap
        print(f"Active source set to: {self.current_source_label}") # Verification/Debug
        self.work_image.display_image(pixmap)
        
        if self.current_source_label == "Box cover":
            self.controls.btn_fix_parallax.setVisible(True)
        else:
            self.controls.btn_fix_parallax.setVisible(False)

    def setup_menu(self):
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help Menu
        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        # Placeholder for about action
        help_menu.addAction(about_action)

    def start_parallax_flow(self):
        self.controls.btn_fix_parallax.setEnabled(False)
        self.work_image.start_parallax_mode()
        
        self.parallax_dialog = ParallaxHelpDialog(self)
        self.parallax_dialog.finished.connect(self.on_parallax_finished)
        self.parallax_dialog.show()

    def on_parallax_finished(self, result):
        if result == QDialog.Accepted:
            coords = self.work_image.get_parallax_coordinates()
            if coords and len(coords) == 4 and hasattr(self, 'current_pixmap') and self.current_pixmap:
                new_pixmap = apply_parallax_correction(self.current_pixmap, coords)
                if new_pixmap:
                    self.current_pixmap = new_pixmap
                    self.work_image.display_image(self.current_pixmap)
                    print(f"Parallax Fixed. Coords: {coords}")
                else:
                    print("Parallax correction failed.")


        else:
            print("Parallax Cancelled")
            
        self.work_image.clear_parallax_selector()
        self.controls.btn_fix_parallax.setEnabled(True)
        self.parallax_dialog = None
