import platform

import cv2


def open_camera(camera_id):
    system = platform.system()

    if system == "Windows":
        return cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    if system == "Darwin":
        return cv2.VideoCapture(camera_id, cv2.CAP_AVFOUNDATION)

    return cv2.VideoCapture(camera_id)
