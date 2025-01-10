import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel
import asyncio
import simpleobsws

class OBSController:
    """Handles OBS WebSocket interactions."""
    def __init__(self, host="localhost", port=4455, password="ukqTwD6rxcFH52PF"):
        self.host = host
        self.port = port
        self.password = password
        
        ws_connection = simpleobsws.WebSocketClient(
            url=f"ws://{host}:{port}",
            password=password
        )
        self.ws = ws_connection
        try:
            asyncio.get_event_loop().run_until_complete(self.ws.connect())
        except Exception as e:
            print(f"Failed to connect to OBS WebSocket: {e}")
            sys.exit(1)

    async def _get_replay_status(self):
        request = simpleobsws.Request('GetReplayBufferStatus')
        ret = await self.ws.call(request)
        return ret.responseData

    async def _get_recording_status(self):
        request = simpleobsws.Request('GetRecordStatus')
        ret = await self.ws.call(request)
        return ret.responseData

    def toggle_replay_buffer(self):
        """Start/stop the replay buffer."""
        try:
            async def toggle():
                status = await self._get_replay_status()
                if status.get('outputActive'):
                    await self.ws.call(simpleobsws.Request('StopReplayBuffer'))
                    return "Replay Buffer Stopped"
                else:
                    await self.ws.call(simpleobsws.Request('StartReplayBuffer'))
                    return "Replay Buffer Started"
            return asyncio.get_event_loop().run_until_complete(toggle())
        except Exception as e:
            return f"Error toggling replay buffer: {e}"

    def save_replay(self):
        """Save the replay buffer."""
        try:
            async def save():
                await self.ws.call(simpleobsws.Request('SaveReplayBuffer'))
                return "Replay Saved"
            return asyncio.get_event_loop().run_until_complete(save())
        except Exception as e:
            return f"Error saving replay: {e}"

    def toggle_recording(self):
        """Start/stop recording."""
        try:
            async def toggle():
                status = await self._get_recording_status()
                if status.get('outputActive'):
                    await self.ws.call(simpleobsws.Request('StopRecord'))
                    return "Recording Stopped"
                else:
                    await self.ws.call(simpleobsws.Request('StartRecord'))
                    return "Recording Started"
            return asyncio.get_event_loop().run_until_complete(toggle())
        except Exception as e:
            return f"Error toggling recording: {e}"

    def disconnect(self):
        """Disconnect from OBS WebSocket."""
        async def close():
            await self.ws.disconnect()
        asyncio.get_event_loop().run_until_complete(close())

class OBSApp(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OBS Controller")
        self.setGeometry(100, 100, 300, 200)
        self.obs = OBSController(password="ukqTwD6rxcFH52PF")

        # Create layout and widgets
        layout = QVBoxLayout()

        self.status_label = QLabel("OBS Controller Ready", self)
        layout.addWidget(self.status_label)

        self.replay_button = QPushButton("Start/Stop Replay Buffer", self)
        self.replay_button.clicked.connect(self.toggle_replay_buffer)
        layout.addWidget(self.replay_button)

        self.save_replay_button = QPushButton("Save Replay", self)
        self.save_replay_button.clicked.connect(self.save_replay)
        layout.addWidget(self.save_replay_button)

        self.record_button = QPushButton("Start/Stop Recording", self)
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        self.view_replay_button = QPushButton("View Latest Replay", self)
        self.view_replay_button.clicked.connect(self.view_latest_replay)
        layout.addWidget(self.view_replay_button)

        # Set central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def toggle_replay_buffer(self):
        status = self.obs.toggle_replay_buffer()
        self.status_label.setText(status)

    def save_replay(self):
        status = self.obs.save_replay()
        self.status_label.setText(status)

    def toggle_recording(self):
        status = self.obs.toggle_recording()
        self.status_label.setText(status)

    def closeEvent(self, event):
        """Clean up resources when closing the application."""
        self.obs.disconnect()
        event.accept()

    def view_latest_replay(self):
        recording_path = "C:/Users/manni/Videos"  # Replace with your recording path
        status = self.obs.open_latest_replay(recording_path)
        self.status_label.setText(status)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OBSApp()
    window.show()
    sys.exit(app.exec())