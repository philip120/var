import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Try MSMF, DSHOW, or VFW
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
cap.set(cv2.CAP_PROP_EXPOSURE, -4)

while True:
    ret, frame = cap.read()
    if ret:
        cv2.imshow("Camera Test", frame)
    else:
        print("Failed to capture frame")
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()