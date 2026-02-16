import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap
from .piece import Piece

def qpixmap_to_opencv(qpixmap: QPixmap) -> np.ndarray:
    """Converts a QPixmap to an OpenCV image (BGR)."""
    qimage = qpixmap.toImage()
    qimage = qimage.convertToFormat(QImage.Format_RGB32)
    
    width = qimage.width()
    height = qimage.height()
    
    ptr = qimage.bits()
    arr = np.array(ptr).reshape(height, width, 4)  # Copies the data
    
    # RGB32 is usually BGR order in OpenCV terms but check format
    # QImage.Format_RGB32 is actually B G R A (0xAARRGGBB in little endian)
    # So arr is BGRA. OpenCV uses BGR.
    return arr[:, :, :3] # Drop Alpha

def detect_pieces(pixmap: QPixmap, min_area=500):
    """
    Detects puzzle pieces from a QPixmap assuming a solid background.
    Returns a list of Piece objects.
    """
    img = qpixmap_to_opencv(pixmap)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Thresholding
    # Assume background is either very dark or very light compared to pieces.
    # We can try OTSU or adaptive. User said "solid background".
    # Let's try Otsu first as it's robust for bimodal histograms.
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Invert if the background is detected as white (pieces are black)
    # Usually we want pieces to be white (255) and background black (0) for findContours
    # Simple check: if corners are white, inverted.
    h, w = thresh.shape
    corners = [thresh[0,0], thresh[0, w-1], thresh[h-1, 0], thresh[h-1, w-1]]
    if sum(corners) / 4 > 127: 
        thresh = cv2.bitwise_not(thresh)
        
    # Morphological operations to close gaps
    kernel = np.ones((3,3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    pieces = []
    piece_id = 1
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
            
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Extract the piece image (ROI)
        piece_img = img[y:y+h, x:x+w].copy()
        
        # Adjust contour to be relative to the piece_img
        cnt_shifted = cnt - [x, y]
        
        new_piece = Piece(piece_id, cnt_shifted, piece_img, origin_offset=(x,y))
        
        # Analyze shape
        analyze_piece(new_piece)
        
        pieces.append(new_piece)
        piece_id += 1
        
    return pieces, thresh # Return thresh for debugging visualization

def analyze_piece(piece: Piece):
    """
    Analyzes the piece contour to identify 4 sides and their types.
    Updates the piece.sides list.
    """
    cnt = piece.contour
    epsilon = 0.04 * cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon, True)
    
    # We expect 4 corners for a standard puzzle piece
    if len(approx) != 4:
        # Fallback: finding 4 extreme points or maybe complex shape
        # For now, if not 4 corners, we skip detailed side analysis or mark as unknown
        # Let's try to enforce 4 corners by finding convex hull or just taking extreme points
        # But for this task, let's assume approxPolyDP works reasonably well for standard pieces
        # If it detects > 4, maybe we can pick the strongest corners?
        # A simple fallback:
        if len(approx) > 4:
            # Sort by distance between points or just pick 4?
            # Or re-approximate with larger epsilon
            pass
        return 
        
    # Order points: Top-Left, Top-Right, Bottom-Right, Bottom-Left
    # Standard trick: sum(x+y) for TL/BR, diff(y-x) for TR/BL
    points = approx.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="int")
    
    s = points.sum(axis=1)
    rect[0] = points[np.argmin(s)] # TL
    rect[2] = points[np.argmax(s)] # BR
    
    diff = np.diff(points, axis=1)
    rect[1] = points[np.argmin(diff)] # TR
    rect[3] = points[np.argmax(diff)] # BL
    
    # Now extract the full contour segments between these corners
    # We need to find the index of these corners in the original contour
    
    # Helper to find closest point index
    def find_index(pt, contour):
        # pt is [x, y]
        # contour is (N, 1, 2)
        dists = np.sum((contour[:, 0, :] - pt)**2, axis=1)
        return np.argmin(dists)
        
    indices = [find_index(pt, cnt) for pt in rect]
    
    # Re-order indices to be sequential (considering wrap-around)
    # The rect extraction does not guarantee order along contour, so let's sort indices?
    # Actually, contour order matters. 
    # Let's re-sort rect based on their appearance in the contour to respect continuous path?
    # No, we want logical sides (Top, Right, Bottom, Left). 
    # So we need to walk from TL -> TR (Top), TR -> BR (Right), etc.
    
    # But contour might be clockwise or counter-clockwise.
    # Check orientation?
    # Assuming standard orientation of contour, let's just use the logic:
    # Top is roughly min-y line?
    
    # Let's trust the TL, TR, BR, BL logic for "sides" mapping.
    # Side 0: TL to TR
    # Side 1: TR to BR
    # Side 2: BR to BL
    # Side 3: BL to TL
    
    from .piece import Side, SideType
    
    for i in range(4):
        p1_idx = indices[i]
        p2_idx = indices[(i+1)%4]
        
        # Extract segment
        if p1_idx < p2_idx:
            segment = cnt[p1_idx:p2_idx+1]
        else: # Wrap around
            segment = np.vstack((cnt[p1_idx:], cnt[:p2_idx+1]))
            
        # Classify Side
        # Check max deviation from line connecting endpoints
        p1 = cnt[p1_idx][0]
        p2 = cnt[p2_idx][0]
        
        # Line equation or distance
        # Simple method: Check center of mass of segment vs line
        # Or peak distance.
        
        # Convert segment to points and rotate so line p1-p2 is X-axis?
        # Simpler: signed distance of point from line.
        
        if len(segment) < 5:
            # Too short, probably flat
            s_type = SideType.FLAT
        else:
            # Calculate distances of all points in segment to line p1-p2
            # Vector p1->p2
            vec = p2 - p1
            # Normal vector (-y, x)
            normal = np.array([-vec[1], vec[0]])
            if np.linalg.norm(normal) > 0:
                normal = normal / np.linalg.norm(normal)
            
            # Vectors from p1 to all points
            vecs = segment[:, 0, :] - p1
            
            # Dot product with normal gives signed distance
            dists = np.dot(vecs, normal)
            
            # Find max deviation (positive and negative)
            max_d = np.max(dists)
            min_d = np.min(dists)
            
            # Threshold (e.g., 15% of side length or fixed pixels)
            side_len = np.linalg.norm(vec)
            threshold = side_len * 0.15 # 15% deviation
            
            # Check for Tab or Socket
            # Convention: Normal points "Outward"? 
            # We need to know if "Outward" is positive or negative.
            # Orientation of contour: usually CCW?
            # If CCW, normal (-dy, dx) points Left of vector p1->p2. 
            # If traversing Top side (Left to Right), Left is Up (Outward).
            # If traversing Right side (Down), Left is Right (Outward).
            # So generally, positive distance is Outward (TAB).
            # Negative distance is Inward (SOCKET).
            
            if max_d > threshold and abs(max_d) > abs(min_d):
                s_type = SideType.TAB
            elif min_d < -threshold and abs(min_d) > abs(max_d):
                s_type = SideType.SOCKET
            else:
                s_type = SideType.FLAT
                
        piece.set_side(i, Side(segment, s_type))

