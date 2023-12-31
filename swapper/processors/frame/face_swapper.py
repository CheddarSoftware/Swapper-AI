from typing import Any, List, Callable
import cv2
import insightface
import threading

import swapper.globals
import swapper.processors.frame.core
from swapper.core import update_status
from swapper.face_analyser import get_one_face, get_many_faces
from swapper.typing import Face, Frame
from swapper.utilities import conditional_download, resolve_relative_path, is_image, is_video, compute_cosine_distance

FACE_SWAPPER = None
THREAD_LOCK = threading.Lock()
NAME = 'Yüz değiştirici'

DIST_THRESHOLD = 0.03


def get_face_swapper() -> Any:
    global FACE_SWAPPER

    with THREAD_LOCK:
        if FACE_SWAPPER is None:
            model_path = resolve_relative_path('../models/inswapper_128.onnx')
            FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=swapper.globals.execution_providers)
    return FACE_SWAPPER


def pre_check() -> bool:
    download_directory_path = resolve_relative_path('../models')
    conditional_download(download_directory_path, ['inswapper_128.onnx'])
    return True


def pre_start() -> bool:
    if not is_image(swapper.globals.source_path):
        update_status('Kaynak yolu için bir görüntü seçin.', NAME)
        return False
    elif not get_one_face(cv2.imread(swapper.globals.source_path)):
        update_status('Kaynak yolunda yüz algılanmadı.', NAME)
        return False
    if not is_image(swapper.globals.target_path) and not is_video(swapper.globals.target_path):
        update_status('Hedef yol için bir resim veya video seçin.', NAME)
        return False
    return True


def post_process() -> None:
    global FACE_SWAPPER

    FACE_SWAPPER = None


def swap_face(source_face: Face, target_face: Face, temp_frame: Frame) -> Frame:
    return get_face_swapper().get(temp_frame, target_face, source_face, paste_back=True)


def process_frame(source_face: Face, target_face: Face, temp_frame: Frame) -> Frame:
    global DIST_THRESHOLD

    if swapper.globals.many_faces:
        many_faces = get_many_faces(temp_frame)
        if many_faces:
            for target_face in many_faces:
                if target_face['det_score'] > 0.65:
                    temp_frame = swap_face(source_face, target_face, temp_frame)
    else:
        if target_face:
            target_embedding = target_face['embedding']
            many_faces = get_many_faces(temp_frame)
            target_face = None
            for dest_face in many_faces:
                dest_embedding = dest_face['embedding']
                if compute_cosine_distance(target_embedding, dest_embedding) <= DIST_THRESHOLD:
                    target_face = dest_face
                    break
            if target_face:
                temp_frame = swap_face(source_face, target_face, temp_frame)
            return temp_frame
                    
        target_face = get_one_face(temp_frame)
        if target_face:
            temp_frame = swap_face(source_face, target_face, temp_frame)
    return temp_frame



def process_frames(source_face: Face, target_face: Face, temp_frame_paths: List[str], update: Callable[[], None]) -> None:
    for temp_frame_path in temp_frame_paths:
        temp_frame = cv2.imread(temp_frame_path)
        result = process_frame(source_face, target_face, temp_frame)
        cv2.imwrite(temp_frame_path, result)
        if update:
            update()


def process_image(source_face: Any, target_face: Any, target_path: str, output_path: str) -> None:
    global DIST_THRESHOLD

    DIST_THRESHOLD = 0.03
    target_frame = cv2.imread(target_path)
    result = process_frame(source_face, target_face, target_frame)
    cv2.imwrite(output_path, result)


def process_video(source_face: Any, target_face: Any, temp_frame_paths: List[str]) -> None:
    global DIST_THRESHOLD

    DIST_THRESHOLD = 0.8
    swapper.processors.frame.core.process_video(source_face, target_face, temp_frame_paths, process_frames)
