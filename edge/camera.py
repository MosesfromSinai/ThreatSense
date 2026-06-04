import platform

import cv2

from config import CAMERA_FPS, FRAME_HEIGHT, FRAME_WIDTH


def configure_camera(camera):
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return camera


def open_camera(camera_id):
    system = platform.system()

    if system == "Windows":
        camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    elif system == "Darwin":
        camera = cv2.VideoCapture(camera_id, cv2.CAP_AVFOUNDATION)
    else:
        camera = cv2.VideoCapture(camera_id)

    return configure_camera(camera)
