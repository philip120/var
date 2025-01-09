from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap

class VideoFeed(QLabel):
    def __init__(self, camera_id: int):
        super().__init__()
        self.camera_id = camera_id
        self.setMinimumSize(QSize(320, 240))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #333;
                background-color: #1a1a1a;
                color: white;
            }
        """)
        self.setText(f"Camera {camera_id}\nNo Signal")

    def update_frame(self, frame):
        if frame is not None:
            height, width = frame.shape[:2]
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio))

class VideoGrid(QWidget):
    def __init__(self, rows: int = 2, cols: int = 2):
        super().__init__()
        self.layout = QGridLayout(self)
        self.layout.setSpacing(10)
        self.feeds = {}
        self.setup_grid(rows, cols)

    def setup_grid(self, rows: int, cols: int):
        # Clear existing feeds
        for feed in self.feeds.values():
            self.layout.removeWidget(feed)
        self.feeds.clear()

        # Create new grid of video feeds
        for row in range(rows):
            for col in range(cols):
                camera_id = row * cols + col
                feed = VideoFeed(camera_id)
                self.feeds[camera_id] = feed
                self.layout.addWidget(feed, row, col)

    def update_feed(self, camera_id: int, frame):
        if camera_id in self.feeds:
            self.feeds[camera_id].update_frame(frame)
