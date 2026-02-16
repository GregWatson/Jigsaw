import cv2
import numpy as np
from enum import Enum

class SideType(Enum):
    FLAT = 0 # Edge of the puzzle
    TAB = 1 # Outward calibration
    SOCKET = 2 # Inward calibration

class Side:
    def __init__(self, contour_segment, side_type=SideType.FLAT):
        self.contour = contour_segment
        self.type = side_type
        self.descriptor = None # To be used for matching (e.g., shape features)

class Piece:
    def __init__(self, piece_id, contour, image, origin_offset=(0,0)):
        """
        :param piece_id: Unique identifier for the piece
        :param contour: Full contour of the piece (in global coordinates or relative? usually relative to the cutout)
        :param image: The cut-out image of the piece (RGBA or masked)
        :param origin_offset: (x, y) offset of this piece's cutout from the original image
        """
        self.id = piece_id
        self.contour = contour
        self.image = image
        self.origin = origin_offset
        self.sides = [None] * 4 # Top, Right, Bottom, Left (or indexed 0-3)
        self.rotation = 0 # 0, 90, 180, 270 (approximate)
        self.center = None # Centroid
        
        # Calculate centroid if contour is provided
        if contour is not None and len(contour) > 0:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                self.center = (cX, cY)

    def set_side(self, index, side: Side):
        if 0 <= index < 4:
            self.sides[index] = side
