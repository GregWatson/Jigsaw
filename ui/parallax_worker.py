
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QImage, QPixmap
import cv2
import numpy as np

class ParallaxHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fix Parallax")
        self.setModal(False) # Non-modal to allow interaction with main window
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        label = QLabel("Drag the yellow handles to select only the image of the jigsaw.\n\nClick Done when selected or ESC to cancel.")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        done_btn = QPushButton("Done")
        done_btn.clicked.connect(self.accept) # Accept triggers close
        layout.addWidget(done_btn)

def apply_parallax_correction(current_pixmap, coords):
    """
    Applies perspective transform to the current_pixmap based on the provided coordinates.
    Returns the corrected QPixmap.
    """
    if not coords or len(coords) != 4 or not current_pixmap:
        return None

    # 1. Prepare Source Points
    src_pts = np.array([(p.x(), p.y()) for p in coords], dtype=np.float32)

    # 2. Compute Bounding Box Dimensions
    min_x = np.min(src_pts[:, 0])
    max_x = np.max(src_pts[:, 0])
    min_y = np.min(src_pts[:, 1])
    max_y = np.max(src_pts[:, 1])
    
    width = int(max_x - min_x)
    height = int(max_y - min_y)

    # 3. Prepare Destination Points (TL, TR, BR, BL)
    # The order of coords from graphics_area is likely TL, TR, BR, BL based on 
    # initialization in start_parallax_mode (p1, p2, p3, p4).
    # However, user might have dragged them around. 
    # For now, we assume the user maintains the relative order or we just map 
    # the current 4 points to the 4 corners of the bounding box.
    # To be robust, we might need to sort them, but let's stick to the previous logic 
    # which assumed a 1-to-1 mapping based on index.
    
    dst_pts = np.array([
        [0, 0],
        [width, 0],
        [width, height],
        [0, height]
    ], dtype=np.float32)

    # 4. Conversion QPixmap -> Numpy
    qimg = current_pixmap.toImage()
    qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
    
    ptr = qimg.constBits()
    h_orig, w_orig = qimg.height(), qimg.width()
    
    # Check if we have valid dimensions
    if h_orig <= 0 or w_orig <= 0:
        return None
        
    arr = np.frombuffer(ptr, np.uint8).reshape(h_orig, w_orig, 4)
    arr = arr.copy() # Make mutable copy

    # 5. Warp
    try:
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(arr, M, (width, height))
    except cv2.error as e:
        print(f"OpenCV Error: {e}")
        return None

    # 6. Conversion Numpy -> QPixmap
    h_new, w_new, ch = warped.shape
    qimg_new = QImage(warped.data, w_new, h_new, w_new * 4, QImage.Format.Format_RGBA8888)
    # Start relying on copies to avoid lifetime issues with numpy buffers
    return QPixmap.fromImage(qimg_new.copy())
