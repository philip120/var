import cv2
import json

def load_config(config_file="config.json"):
    with open(config_file, "r") as file:
        return json.load(file)

def test_camera():
    # Load configuration
    config = load_config()
    camera_source = config.get("camera_source", 0)
    frame_width = config.get("frame_width", 640)
    frame_height = config.get("frame_height", 480)
    frame_rate = config.get("frame_rate", 30)

    # Open the video source
    cap = cv2.VideoCapture(camera_source)

    if not cap.isOpened():
        print(f"Error: Unable to access camera (source: {camera_source})")
        return

    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    cap.set(cv2.CAP_PROP_FPS, frame_rate)

    print(f"Camera {camera_source} opened successfully.")
    print("Press 'q' to quit the video preview.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        cv2.imshow("Camera Test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting camera test...")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_camera()
