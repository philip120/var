# src/ui/camera_selection_dialog.py

import logging
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
from utils.camera_utils import get_available_cameras

logger = logging.getLogger(__name__)

class CameraSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Camera")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create list widget
        self.camera_list = QListWidget()
        layout.addWidget(self.camera_list)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Create buttons
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.populate_camera_list)
        self.select_btn = QPushButton("Select")
        self.select_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        # Add buttons to layout
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.cancel_btn)
        
        # Add button layout to main layout
        layout.addLayout(button_layout)
        
        # Populate camera list
        self.populate_camera_list()
        
    def populate_camera_list(self):
        """Populate the list of available cameras"""
        try:
            self.camera_list.clear()
            cameras = get_available_cameras(max_cameras=4)
            
            for idx, available, info in cameras:
                if available and info is not None:
                    width, height, fps = info
                    self.camera_list.addItem(f"Camera {idx} ({width}x{height}, {fps} FPS)")
                    
            # Select first item if available
            if self.camera_list.count() > 0:
                self.camera_list.setCurrentRow(0)
                
        except Exception as e:
            logger.error(f"Error populating camera list: {str(e)}", exc_info=True)
            
    def get_selected_camera(self) -> int:
        """Get the selected camera index"""
        try:
            current_item = self.camera_list.currentItem()
            if current_item is not None:
                # Extract camera index from text (e.g., "Camera 0 (640x480, 30 FPS)")
                text = current_item.text()
                camera_idx = int(text.split()[1])  # Get the number after "Camera"
                return camera_idx
        except Exception as e:
            logger.error(f"Error getting selected camera: {str(e)}", exc_info=True)
        return None
