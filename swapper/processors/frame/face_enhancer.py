from typing import Any, List, Callable
import cv2
import threading
import gfpgan

import swapper.globals
import swapper.processors.frame.core
from swapper.core import update_status
from swapper.face_analyser import get_one_face
from swapper.typing import Frame, Face
from swapper.utilities import conditional_download, resolve_relative_path, is_image, is_video
from PIL import Image
from numpy import asarray

FACE_ENHANCER = None
THREAD_SEMAPHORE = threading.Semaphore()
THREAD_LOCK = threading.Lock()
NAME = 'Yüz geliştirici'


def get_face_enhancer() -> Any:
    global FACE_ENHANCER

    with THREAD_LOCK:
        if FACE_ENHANCER is None:
            model_path = resolve_relative_path('../models/GFPGANv1.4.pth')
            FACE_ENHANCER = gfpgan.GFPGANer(model_path=model_path, upscale=1)
    return FACE_ENHANCER


def pre_check() -> bool:
    download_directory_path = resolve_relative_path('../models')
    conditional_download(download_directory_path, ['GFPGANv1.4.pth'])
    return True


def pre_start() -> bool:
    if not is_image(swapper.globals.target_path) and not is_video(swapper.globals.target_path):
        update_status('Hedef yol için bir resim veya video seçin.', NAME)
        return False
    return True


def post_process() -> None:
    global FACE_ENHANCER

    FACE_ENHANCER = None


def enhance_face(temp_frame: Frame) -> Frame:
    with THREAD_SEMAPHORE:
        temp_frame_original = Image.fromarray(temp_frame)
        _, _, temp_frame = get_face_enhancer().enhance(
            temp_frame,
            paste_back=True
        )
        temp_frame = Image.blend(temp_frame_original, Image.fromarray(temp_frame), 0.75)
    return asarray(temp_frame)

def process_frame(source_path: str, temp_frame: Frame) -> Frame:
    target_face = get_one_face(temp_frame)
    if target_face:
        temp_frame = enhance_face(temp_frame)
    return temp_frame


def process_frames(source_face: Face, target_face: Face, temp_frame_paths: List[str], update: Callable[[], None]) -> None:
    for temp_frame_path in temp_frame_paths:
        temp_frame = cv2.imread(temp_frame_path)
        result = process_frame(None, temp_frame)
        cv2.imwrite(temp_frame_path, result)
        if update:
            update()


def process_image(source_face: Face, target_face: Face, target_path: str, output_path: str) -> None:
    target_frame = cv2.imread(target_path)
    result = process_frame(None, target_frame)
    cv2.imwrite(output_path, result)


def process_video(source_face: Any, target_face: Any, temp_frame_paths: List[str]) -> None:
    swapper.processors.frame.core.process_video(source_face, target_face, temp_frame_paths, process_frames)
