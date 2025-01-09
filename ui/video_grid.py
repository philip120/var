import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap
import logging

logger = logging.getLogger(__name__)

class VideoLabel(QLabel):
    def __init__(self, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self.setMinimumSize(QSize(320, 240))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("QLabel { background-color: #808080; color: white; }")
        self.setText(f"Camera {camera_id}\nNo Signal")
        self._current_frame = None
        self._current_size = None
        self._current_pixmap = None
        self.setMinimumHeight(240)
        self.setMinimumWidth(320)
        
    def update_frame(self, frame):
        """Update the video feed with a new frame"""
        if frame is None:
            return
            
        try:
            # Store current frame
            if self._current_frame is None or not np.array_equal(frame, self._current_frame):
                self._current_frame = frame.copy()
                
                # Get current size for scaling
                w = self.width()
                h = self.height()
                
                if w <= 0 or h <= 0:
                    return
                    
                # Only resize if size changed or frame changed
                if self._current_size != (w, h) or self._current_pixmap is None:
                    self._current_size = (w, h)
                    
                    # Calculate target size maintaining aspect ratio
                    frame_h, frame_w = frame.shape[:2]
                    aspect = frame_w / frame_h
                    
                    if w/h > aspect:
                        new_w = int(h * aspect)
                        new_h = h
                    else:
                        new_w = w
                        new_h = int(w / aspect)
                        
                    # Resize frame efficiently
                    resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                    
                    # Ensure the frame is in the correct format (RGB, uint8)
                    if resized_frame.dtype != np.uint8:
                        resized_frame = resized_frame.astype(np.uint8)
                    if len(resized_frame.shape) == 2:  # Grayscale
                        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_GRAY2RGB)
                    elif resized_frame.shape[2] == 3:  # BGR
                        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                    
                    # Create QImage with correct format and stride
                    height, width = resized_frame.shape[:2]
                    bytes_per_line = width * 3
                    q_img = QImage(resized_frame.data, width, height, 
                                 bytes_per_line, QImage.Format.Format_RGB888)
                    
                    # Create new pixmap
                    self._current_pixmap = QPixmap.fromImage(q_img)
                
                # Always update the display if we have a pixmap
                if self._current_pixmap is not None:
                    self.setPixmap(self._current_pixmap)
                    self.setText("")  # Clear any error text
            
        except Exception as e:
            logger.error(f"Error updating frame for camera {self.camera_id}: {str(e)}")
            self.setText(f"Camera {self.camera_id}\nError")
            
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        # Force resize on next frame
        self._current_size = None
        if self._current_frame is not None:
            self.update_frame(self._current_frame)

class VideoGrid(QWidget):
    def __init__(self, rows=2, cols=2):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.logger = logging.getLogger(f"{__name__}.VideoGrid")
        
        # Create grid layout
        self.grid = QGridLayout(self)
        self.grid.setSpacing(5)
        self.grid.setContentsMargins(0, 0, 0, 0)
        
        # Initialize video labels
        self.video_labels = {}
        for row in range(rows):
            for col in range(cols):
                camera_id = row * cols + col
                label = VideoLabel(camera_id)
                self.grid.addWidget(label, row, col)
                self.video_labels[camera_id] = label
                
        self.logger.debug(f"Created video grid with {rows}x{cols} layout")
        
    def update_feed(self, camera_id: int, frame: np.ndarray):
        """Update the video feed for a specific camera"""
        try:
            if camera_id not in self.video_labels:
                return
            self.video_labels[camera_id].update_frame(frame)
        except Exception as e:
            self.logger.error(f"Error updating feed for camera {camera_id}: {str(e)}", exc_info=True)
    
    def clear_feed(self, camera_id: int):
        """Clear the video feed for a specific camera"""
        try:
            if camera_id in self.video_labels:
                label = self.video_labels[camera_id]
                label.clear()
                label._current_frame = None
                label._current_size = None
                label.setText(f"Camera {camera_id}\nNo Signal")
        except Exception as e:
            self.logger.error(f"Error clearing feed for camera {camera_id}: {str(e)}")
