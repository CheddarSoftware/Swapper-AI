import os
import sys
if any(arg.startswith('--execution-provider') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import warnings
from typing import List
import platform
import signal
import shutil
import argparse
import torch
import onnxruntime
import tensorflow

import swapper.globals
import swapper.metadata
import swapper.ui as ui
from swapper.processors.frame.core import get_frame_processors_modules
from swapper.utilities import has_image_extension, is_image, is_video, detect_fps, create_video, extract_frames, get_temp_frame_paths, restore_audio, create_temp, move_temp, clean_temp, normalize_output_path

if 'ROCMExecutionProvider' in swapper.globals.execution_providers:
    del torch

warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')
warnings.filterwarnings('ignore', category=UserWarning, module='torchvision')


def parse_args() -> None:
    signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())
    program = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100))
    program.add_argument('-s', '--source', help='select an source image', dest='source_path')
    program.add_argument('-t', '--target', help='select an target image or video', dest='target_path')
    program.add_argument('-o', '--output', help='select output file or directory', dest='output_path')
    program.add_argument('--frame-processor', help='frame processors (choices: face_swapper, face_enhancer, ...)', dest='frame_processor', default=['face_swapper'], nargs='+')
    program.add_argument('--keep-fps', help='keep original fps', dest='keep_fps', action='store_true', default=False)
    program.add_argument('--keep-audio', help='keep original audio', dest='keep_audio', action='store_true', default=True)
    program.add_argument('--keep-frames', help='keep temporary frames', dest='keep_frames', action='store_true', default=False)
    program.add_argument('--many-faces', help='process every face', dest='many_faces', action='store_true', default=False)
    program.add_argument('--video-encoder', help='adjust output video encoder', dest='video_encoder', default='libx264', choices=['libx264', 'libx265', 'libvpx-vp9'])
    program.add_argument('--video-quality', help='adjust output video quality', dest='video_quality', type=int, default=18, choices=range(52), metavar='[0-51]')
    program.add_argument('--max-memory', help='maximum amount of RAM in GB', dest='max_memory', type=int, default=suggest_max_memory())
    program.add_argument('--execution-provider', help='available execution provider (choices: cpu, ...)', dest='execution_provider', default=['cpu'], choices=suggest_execution_providers(), nargs='+')
    program.add_argument('--execution-threads', help='number of execution threads', dest='execution_threads', type=int, default=suggest_execution_threads())
    program.add_argument('-v', '--version', action='version', version=f'{swapper.metadata.name} {swapper.metadata.version}')

    args = program.parse_args()

    swapper.globals.source_path = args.source_path
    swapper.globals.target_path = args.target_path
    swapper.globals.output_path = normalize_output_path(swapper.globals.source_path, swapper.globals.target_path, args.output_path)
    swapper.globals.frame_processors = args.frame_processor
    swapper.globals.headless = args.source_path or args.target_path or args.output_path
    swapper.globals.keep_fps = args.keep_fps
    swapper.globals.keep_audio = args.keep_audio
    swapper.globals.keep_frames = args.keep_frames
    swapper.globals.many_faces = args.many_faces
    swapper.globals.video_encoder = args.video_encoder
    swapper.globals.video_quality = args.video_quality
    swapper.globals.max_memory = args.max_memory
    swapper.globals.execution_providers = decode_execution_providers(args.execution_provider)
    swapper.globals.execution_threads = args.execution_threads


def encode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers]


def decode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [provider for provider, encoded_execution_provider in zip(onnxruntime.get_available_providers(), encode_execution_providers(onnxruntime.get_available_providers()))
            if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers)]


def suggest_max_memory() -> int:
    if platform.system().lower() == 'darwin':
        return 4
    return 16


def suggest_execution_providers() -> List[str]:
    return encode_execution_providers(onnxruntime.get_available_providers())


def suggest_execution_threads() -> int:
    if 'DmlExecutionProvider' in swapper.globals.execution_providers:
        return 1
    if 'ROCMExecutionProvider' in swapper.globals.execution_providers:
        return 1
    return 8


def limit_resources() -> None:
    gpus = tensorflow.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tensorflow.config.experimental.set_virtual_device_configuration(gpu, [
            tensorflow.config.experimental.VirtualDeviceConfiguration(memory_limit=1024)
        ])
    if swapper.globals.max_memory:
        memory = swapper.globals.max_memory * 1024 ** 3
        if platform.system().lower() == 'darwin':
            memory = swapper.globals.max_memory * 1024 ** 6
        if platform.system().lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def release_resources() -> None:
    if 'CUDAExecutionProvider' in swapper.globals.execution_providers:
        torch.cuda.empty_cache()


def pre_check() -> bool:
    if sys.version_info < (3, 9):
        update_status('Python version is not supported - please upgrade to 3.9 or higher.')
        return False
    return True


def update_status(message: str, scope: str = 'swapper.CORE') -> None:
    print(f'[{scope}] {message}')
    if not swapper.globals.headless:
        ui.update_status(message)



def start() -> None:
    for frame_processor in get_frame_processors_modules(swapper.globals.frame_processors):
        if not frame_processor.pre_start():
            return
    if has_image_extension(swapper.globals.target_path):

        for frame_processor in get_frame_processors_modules(swapper.globals.frame_processors):
            target = swapper.globals.target_path
            if frame_processor.NAME == 'Yüz geliştirici':
                if not swapper.globals.post_enhance:
                    continue
                target = swapper.globals.output_path

            update_status(f'{frame_processor.NAME} yürütülüyor...')
            frame_processor.process_image(ui.SELECTED_FACE_DATA_INPUT, ui.SELECTED_FACE_DATA_OUTPUT, target, swapper.globals.output_path)
            frame_processor.post_process()
            release_resources()
        if is_image(swapper.globals.target_path):
            update_status('Görüntü işleme başarılı!')
        else:
            update_status('Görüntü işleme başarısız oldu!')
        return

    update_status('Geçici kaynaklar oluşturuluyor...')
    create_temp(swapper.globals.target_path)
    update_status('Kareler ayıklanıyor...')
    extract_frames(swapper.globals.target_path)
    temp_frame_paths = get_temp_frame_paths(swapper.globals.target_path)
    for frame_processor in get_frame_processors_modules(swapper.globals.frame_processors):
        if frame_processor.NAME == 'Yüz geliştirici' and not swapper.globals.post_enhance:
            continue

        update_status(f'{frame_processor.NAME} yürütülüyor...')
        frame_processor.process_video(ui.SELECTED_FACE_DATA_INPUT, ui.SELECTED_FACE_DATA_OUTPUT, temp_frame_paths)
        frame_processor.post_process()
        release_resources()

    if swapper.globals.keep_fps:
        update_status('FPS değeri tespit ediliyor...')
        fps = detect_fps(swapper.globals.target_path)
        update_status(f'{fps} FPS ile video oluşturuluyor...')
        create_video(swapper.globals.target_path, fps)
    else:
        update_status('30 FPS ile video oluşturuluyor...')
        create_video(swapper.globals.target_path)

    if swapper.globals.keep_audio:
        if swapper.globals.keep_fps:
            update_status('Ses geri yükleniyor...')
        else:
            update_status('Sesi geri yüklemek, FPS korunmadığından sorunlara neden olabilir...')
        restore_audio(swapper.globals.target_path, swapper.globals.output_path)
    else:
        move_temp(swapper.globals.target_path, swapper.globals.output_path)

    clean_temp(swapper.globals.target_path)
    if is_video(swapper.globals.target_path):
        update_status('Video işleme başarılı!')
    else:
        update_status('Video işleme başarısız oldu!')


def destroy() -> None:
    if swapper.globals.target_path:
        clean_temp(swapper.globals.target_path)
    quit()


def run() -> None:
    parse_args()
    if not pre_check():
        return
    for frame_processor in get_frame_processors_modules(swapper.globals.frame_processors):
        if not frame_processor.pre_check():
            return
    limit_resources()
    if swapper.globals.headless:
        start()
    else:
        window = ui.init(start, destroy)
        window.mainloop()
