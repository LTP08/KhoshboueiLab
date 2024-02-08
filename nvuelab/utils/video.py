from datetime import datetime
import cv2 as cv
import PySpin


def show(img):
    cv.imshow("Live Video", img)


def video_writer_init(filename, fps, frame_width, frame_height):
    fourcc = cv.VideoWriter_fourcc(*"mp4v")
    return cv.VideoWriter(filename, fourcc, fps, (frame_width, frame_height), False)


def save_video(video_writer, img):
    video_writer.write(img)
