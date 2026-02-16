import cv2
import numpy as np
from .piece import Piece, SideType

def find_matches(pieces: list[Piece]):
    """
    Iterates through pieces and finds matches between Tabs and Sockets.
    Returns a list of matches: [(piece1, side_idx1, piece2, side_idx2, score), ...]
    """
    matches = []
    
    # Simple exhaustive search
    # In a real app, use spatial hashing or filter by side length first
    
    for i, p1 in enumerate(pieces):
        for s1_idx, side1 in enumerate(p1.sides):
            if side1 is None or side1.type == SideType.FLAT:
                continue
                
            # We only look for matches for Sockets (to avoid duplicates, 
            # or handle both but be careful).
            # Let's say we look for a match for any non-flat side.
            # If side1 is SOCKET, we look for TAB.
            # If side1 is TAB, we look for SOCKET.
            
            target_type = SideType.TAB if side1.type == SideType.SOCKET else SideType.SOCKET
            
            for j, p2 in enumerate(pieces):
                if i == j: 
                    continue
                    
                for s2_idx, side2 in enumerate(p2.sides):
                    if side2 is None or side2.type != target_type:
                        continue
                        
                    # Check compatibility
                    
                    # 1. Length check
                    # Length of vector between endpoints
                    l1 = np.linalg.norm(side1.contour[0][0] - side1.contour[-1][0])
                    l2 = np.linalg.norm(side2.contour[0][0] - side2.contour[-1][0])
                    
                    if abs(l1 - l2) > 100: # Threshold in pixels (fairly loose)
                        continue
                        
                    # 2. Shape matching
                    # cv2.matchShapes returns a metric (lower is better)
                    # We might need to rotate side2 to match orientation of side1?
                    # matchShapes is rotation invariant!
                    
                    score = cv2.matchShapes(side1.contour, side2.contour, cv2.CONTOURS_MATCH_I1, 0)
                    
                    if score < 0.1: # Threshold (experimental)
                        # High quality match
                        matches.append({
                            "p1": p1, "s1": s1_idx,
                            "p2": p2, "s2": s2_idx,
                            "score": score
                        })
                        
    # Sort by best score
    matches.sort(key=lambda x: x["score"])
    
    return matches
