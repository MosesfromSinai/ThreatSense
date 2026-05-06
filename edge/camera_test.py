import cv2

def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: could not open webcam")
        return

    print("Webcam started. Press q to quit.")

    while True:
        ret, frame = camera.read()

        if not ret:
            print("Error: could not read frame")
            break

        cv2.imshow("ThreatSense Camera Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()