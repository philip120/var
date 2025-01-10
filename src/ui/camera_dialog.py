# src/ui/camera_selection_dialog.py

import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QPushButton, 
                          QHBoxLayout, QLabel, QListWidgetItem)
from PyQt6.QtCore import Qt
from utils.camera_utils import get_available_cameras

logger = logging.getLogger(__name__)

class CameraSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Cameras")
        self.setMinimumWidth(500)
        
        # Store selected cameras
        self.selected_cameras = []
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add instruction label
        self.status_label = QLabel("Select up to 2 cameras:")
        layout.addWidget(self.status_label)
        
        # Create list widget with checkboxes
        self.camera_list = QListWidget()
        self.camera_list.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.camera_list)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Create buttons
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.populate_camera_list)
        self.select_btn = QPushButton("Done")
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
                    item = QListWidgetItem(f"Camera {idx} ({width}x{height}, {fps} FPS)")
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    self.camera_list.addItem(item)
                    
        except Exception as e:
            logger.error(f"Error populating camera list: {str(e)}", exc_info=True)
            
    def on_item_changed(self, item):
        """Handle camera selection changes"""
        try:
            # Get camera index from item text
            text = item.text()
            camera_idx = int(text.split()[1])
            
            if item.checkState() == Qt.CheckState.Checked:
                # Add camera if not already selected and limit to 2 cameras
                if camera_idx not in self.selected_cameras:
                    if len(self.selected_cameras) < 2:
                        self.selected_cameras.append(camera_idx)
                    else:
                        # Uncheck if already have 2 cameras
                        item.setCheckState(Qt.CheckState.Unchecked)
            else:
                # Remove camera if unchecked
                if camera_idx in self.selected_cameras:
                    self.selected_cameras.remove(camera_idx)
                    
            # Update status label
            if len(self.selected_cameras) == 0:
                self.status_label.setText("Select up to 2 cameras:")
            elif len(self.selected_cameras) == 1:
                self.status_label.setText("Selected Camera: " + str(self.selected_cameras[0]) + 
                                        " (select another or click Done)")
            else:
                self.status_label.setText("Selected Cameras: " + 
                                        str(self.selected_cameras[0]) + " and " + 
                                        str(self.selected_cameras[1]))
                
        except Exception as e:
            logger.error(f"Error handling camera selection: {str(e)}", exc_info=True)
            
    def get_selected_cameras(self):
        """Get list of selected camera indices"""
        return self.selected_cameras.copy() if self.selected_cameras else None
