import numpy as np
import cv2
import face_recognition
import os
from datetime import datetime

path = 'ImagesAttendance'
images = []
classNames = []
myList = os.listdir(path)

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    if curImg is not None:
        images.append(curImg)
        classNames.append(os.path.splitext(cl)[0])

def findEncodings(images):
    encodeList = []
    for img in images:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_img)
        if encodings:
            encodeList.append(encodings[0])
    return encodeList

def markAttendance(name):
    with open('Attendance.csv', 'r+') as f:
        nameList = [line.split(',')[0] for line in f.readlines()]
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.write(f'\n{name},{dtString}')

encodeListKnown = findEncodings(images)
print('Encoding Complete')

print("\nAvailable Filter Keys:")
print("g - Grayscale")
print("e - Histogram Equalization")
print("s - Gaussian Blur")
print("m - Median Blur")
print("b - Bilateral Filter")
print("c - Canny Edge Detection")
print("l - Laplacian Edge Detection")
print("x - Sobel X")
print("y - Sobel Y")
print("d - Dilation")
print("r - Erosion")
print("z - Morphological Gradient")
print("h - Adaptive Thresholding")
print("w - Image Sharpening")
print("o - Original Image")
print("p - Save Screenshot")
print("q - Quit\n")

cap = cv2.VideoCapture(0)
filter_mode = 'original'
screenshot_count = 0

while True:
    success, img = cap.read()
    if not success:
        break

    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgEqualized = cv2.equalizeHist(imgGray)
    imgBlurred = cv2.GaussianBlur(img, (5, 5), 0)
    imgMedianBlur = cv2.medianBlur(img, 5)
    imgBilateral = cv2.bilateralFilter(img, 9, 75, 75)
    imgCanny = cv2.Canny(img, 100, 200)
    laplacian = cv2.Laplacian(imgGray, cv2.CV_64F)
    sobelX = cv2.Sobel(imgGray, cv2.CV_64F, 1, 0, ksize=5)
    sobelY = cv2.Sobel(imgGray, cv2.CV_64F, 0, 1, ksize=5)

    kernel = np.ones((5, 5), np.uint8)
    dilation = cv2.dilate(imgCanny, kernel, iterations=1)
    erosion = cv2.erode(imgCanny, kernel, iterations=1)
    morph_gradient = cv2.morphologyEx(imgGray, cv2.MORPH_GRADIENT, kernel)
    adaptive_thresh = cv2.adaptiveThreshold(imgGray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY, 11, 2)

    sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(img, -1, sharpen_kernel)

    small_frame = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    facesCurFrame = face_recognition.face_locations(rgb_small_frame)
    encodesCurFrame = face_recognition.face_encodings(rgb_small_frame, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        if len(faceDis) > 0:
            matchIndex = np.argmin(faceDis)
            if matches[matchIndex]:
                name = classNames[matchIndex].upper()
                y1, x2, y2, x1 = [val * 4 for val in faceLoc]
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                markAttendance(name)

    if filter_mode == 'gray':
        cv2.imshow("Filter View", imgGray)
    elif filter_mode == 'equalized':
        cv2.imshow("Filter View", imgEqualized)
    elif filter_mode == 'gaussian':
        cv2.imshow("Filter View", imgBlurred)
    elif filter_mode == 'median':
        cv2.imshow("Filter View", imgMedianBlur)
    elif filter_mode == 'bilateral':
        cv2.imshow("Filter View", imgBilateral)
    elif filter_mode == 'canny':
        cv2.imshow("Filter View", imgCanny)
    elif filter_mode == 'laplacian':
        cv2.imshow("Filter View", laplacian.astype(np.uint8))
    elif filter_mode == 'sobelx':
        cv2.imshow("Filter View", sobelX.astype(np.uint8))
    elif filter_mode == 'sobely':
        cv2.imshow("Filter View", sobelY.astype(np.uint8))
    elif filter_mode == 'dilation':
        cv2.imshow("Filter View", dilation)
    elif filter_mode == 'erosion':
        cv2.imshow("Filter View", erosion)
    elif filter_mode == 'morph':
        cv2.imshow("Filter View", morph_gradient)
    elif filter_mode == 'adaptive':
        cv2.imshow("Filter View", adaptive_thresh)
    elif filter_mode == 'sharpen':
        cv2.imshow("Filter View", sharpened)
    else:
        cv2.imshow("Filter View", img)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('g'):
        filter_mode = 'gray'
    elif key == ord('e'):
        filter_mode = 'equalized'
    elif key == ord('s'):
        filter_mode = 'gaussian'
    elif key == ord('m'):
        filter_mode = 'median'
    elif key == ord('b'):
        filter_mode = 'bilateral'
    elif key == ord('c'):
        filter_mode = 'canny'
    elif key == ord('l'):
        filter_mode = 'laplacian'
    elif key == ord('x'):
        filter_mode = 'sobelx'
    elif key == ord('y'):
        filter_mode = 'sobely'
    elif key == ord('d'):
        filter_mode = 'dilation'
    elif key == ord('r'):
        filter_mode = 'erosion'
    elif key == ord('z'):
        filter_mode = 'morph'
    elif key == ord('h'):
        filter_mode = 'adaptive'
    elif key == ord('w'):
        filter_mode = 'sharpen'
    elif key == ord('o'):
        filter_mode = 'original'
    elif key == ord('p'):
        cv2.imwrite(f'screenshot_{screenshot_count}.png', img)
        screenshot_count += 1
        print("Screenshot saved.")

cap.release()
cv2.destroyAllWindows()

#/opt/anaconda3/bin/python "/Users/anjul/Desktop/Facial Recognition & Attendance System/AttendanceProject.py"
#cap = cv2.VideoCapture(0)
