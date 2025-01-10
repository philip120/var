import cv2

def list_cameras():
    """List available cameras and their details."""
    print("Scanning for connected cameras...")
    for device_index in range(10):  # Test indices 0 to 9
        cap = cv2.VideoCapture(device_index)
        if cap.isOpened():
            print(f"Device Index: {device_index}")
            
            # Retrieve camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            print(f"  Resolution: {width}x{height}")
            print(f"  FPS: {fps}")
            
            cap.release()
        else:
            print(f"Device Index {device_index} is not available.")

if __name__ == "__main__":
    list_cameras()
