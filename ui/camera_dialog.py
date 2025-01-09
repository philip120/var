from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QListWidget, QListWidgetItem, QLabel)
from PyQt6.QtCore import Qt
import cv2
import platform

class CameraSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Camera")
        self.setMinimumWidth(400)
        self.selected_camera = None
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add description
        layout.addWidget(QLabel("Available Video Devices:"))
        
        # Create list widget
        self.camera_list = QListWidget()
        layout.addWidget(self.camera_list)
        
        # Add buttons
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.populate_cameras)
        self.select_btn = QPushButton("Select")
        self.select_btn.clicked.connect(self.accept_selection)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # Populate the list
        self.populate_cameras()
    
    def get_video_devices(self):
        """Get list of video devices"""
        devices = []
        
        # Try indices from 0 to 9
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Try to read a frame to confirm it's working
                ret, _ = cap.read()
                if ret:
                    # Get camera name if possible
                    if platform.system() == 'Windows':
                        devices.append({
                            'name': f'Camera {i}',
                            'path': i
                        })
                    else:
                        devices.append({
                            'name': f'Camera {i}',
                            'path': f'/dev/video{i}'
                        })
                cap.release()
        
        return devices
    
    def populate_cameras(self):
        """Populate the list with available cameras"""
        self.camera_list.clear()
        devices = self.get_video_devices()
        
        for device in devices:
            item = QListWidgetItem(f"{device['name']}")
            item.setData(Qt.ItemDataRole.UserRole, device['path'])
            self.camera_list.addItem(item)
            
        if self.camera_list.count() == 0:
            self.camera_list.addItem("No cameras found")
    
    def accept_selection(self):
        """Handle camera selection"""
        current_item = self.camera_list.currentItem()
        if current_item and current_item.text() != "No cameras found":
            self.selected_camera = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()
        
    def get_selected_camera(self):
        """Return the selected camera device path"""
        return self.selected_camera 