import cv2
from typing import List, Tuple

def get_available_cameras(max_cameras: int = 5) -> List[Tuple[int, bool]]:
    """
    Scan for available cameras on the system.
    
    Args:
        max_cameras: Maximum number of cameras to check
        
    Returns:
        List of tuples containing (camera_index, is_available)
    """
    available_cameras = []
    
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            available_cameras.append((i, ret))
        else:
            available_cameras.append((i, False))
        cap.release()
    
    return available_cameras 