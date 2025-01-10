import cv2

def test_camera(camera_source=0):
    # Open the video source (default: 0 for local webcam)
    cap = cv2.VideoCapture(camera_source)

    if not cap.isOpened():
        print(f"Error: Unable to access camera (source: {camera_source})")
        return

    print(f"Camera {camera_source} opened successfully.")
    print("Press 'q' to quit the video preview.")

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Display the resulting frame
        cv2.imshow("Camera Test", frame)

        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting camera test...")
            break

    # Release the capture object and close the display window
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Call the function to test the camera
    test_camera()
