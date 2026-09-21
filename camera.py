import cv2

cap = cv2.VideoCapture(0)  # Attempt to access the default camera

if not cap.isOpened():
    print("Camera not found or failed to open.")
else:
    print("Camera is working.")
    cap.release()
