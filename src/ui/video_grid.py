import cv2
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

class VideoGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(5)
        self.feeds = {}  # Dictionary to store feed widgets
        
    def setup_grid(self, num_cameras):
        """Setup the grid layout based on number of cameras"""
        # Clear existing feeds
        for feed in self.feeds.values():
            self.layout.removeWidget(feed)
            feed.deleteLater()
        self.feeds.clear()
        
        if num_cameras == 1:
            # Single camera - one large feed
            feed = QLabel()
            feed.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(feed, 0, 0)
            self.feeds[0] = feed
            
        elif num_cameras == 2:
            # Two cameras - side by side
            for i in range(2):
                feed = QLabel()
                feed.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.layout.addWidget(feed, 0, i)
                self.feeds[i] = feed
                
    def update_feed(self, camera_idx, frame):
        """Update the video feed for a specific camera"""
        if camera_idx in self.feeds and frame is not None:
            try:
                # Get feed dimensions
                feed = self.feeds[camera_idx]
                w = feed.width()
                h = feed.height()
                
                if w > 0 and h > 0:
                    # Scale frame to fit feed while maintaining aspect ratio
                    frame_h, frame_w = frame.shape[:2]
                    scale = min(w/frame_w, h/frame_h)
                    new_w = int(frame_w * scale)
                    new_h = int(frame_h * scale)
                    
                    # Resize frame
                    frame = cv2.resize(frame, (new_w, new_h))
                    
                    # Convert frame to QImage
                    bytes_per_line = frame.strides[0]
                    image = QImage(frame.data, frame.shape[1], frame.shape[0], 
                    bytes_per_line, QImage.Format.Format_BGR888)
                    
                    # Convert to pixmap and set to label
                    pixmap = QPixmap.fromImage(image)
                    feed.setPixmap(pixmap)
                    
            except Exception as e:
                print(f"Error updating feed {camera_idx}: {str(e)}")
                
    def clear_feed(self, camera_idx):
        """Clear the video feed for a specific camera"""
        if camera_idx in self.feeds:
            self.feeds[camera_idx].clear()
