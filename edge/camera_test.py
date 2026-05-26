import argparse

import cv2

from camera import open_camera
from config import CAMERA_ID


def main():
    parser = argparse.ArgumentParser(description="Test the ThreatSense camera feed.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Read one frame and exit without opening a preview window.",
    )
    args = parser.parse_args()

    camera = open_camera(CAMERA_ID)

    if not camera.isOpened():
        print(f"Error: could not open webcam at CAMERA_ID={CAMERA_ID}")
        return

    if args.once:
        ret, frame = camera.read()
        camera.release()

        if not ret:
            print(f"Error: could not read frame from CAMERA_ID={CAMERA_ID}")
            return

        height, width = frame.shape[:2]
        print(f"Camera OK at CAMERA_ID={CAMERA_ID}: {width}x{height}")
        return

    print(f"Webcam started at CAMERA_ID={CAMERA_ID}. Press q to quit.")

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
