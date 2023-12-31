import os
import importlib
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from types import ModuleType
from typing import Any, List, Callable
from swapper.typing import Face
from tqdm import tqdm

import swapper

FRAME_PROCESSORS_MODULES: List[ModuleType] = []
FRAME_PROCESSORS_INTERFACE = [
    'pre_check',
    'pre_start',
    'process_frame',
    'process_frames',
    'process_image',
    'process_video',
    'post_process'
]


def load_frame_processor_module(frame_processor: str) -> Any:
    try:
        frame_processor_module = importlib.import_module(f'swapper.processors.frame.{frame_processor}')
        for method_name in FRAME_PROCESSORS_INTERFACE:
            if not hasattr(frame_processor_module, method_name):
                raise NotImplementedError
    except (ImportError, NotImplementedError):
        quit(f'{frame_processor} kare işlemcisi kilitlendi.')
    return frame_processor_module


def get_frame_processors_modules(frame_processors: List[str]) -> List[ModuleType]:
    global FRAME_PROCESSORS_MODULES

    if not FRAME_PROCESSORS_MODULES:
        for frame_processor in frame_processors:
            frame_processor_module = load_frame_processor_module(frame_processor)
            FRAME_PROCESSORS_MODULES.append(frame_processor_module)
    return FRAME_PROCESSORS_MODULES


def multi_process_frame(source_face: Face, target_face: Face, temp_frame_paths: List[str], process_frames: Callable[[str, List[str], Any], None], update: Callable[[], None]) -> None:
    with ThreadPoolExecutor(max_workers=swapper.globals.execution_threads) as executor:
        futures = []
        queue = create_queue(temp_frame_paths)
        total = len(temp_frame_paths)
        queue_per_future = total // swapper.globals.execution_threads
        while not queue.empty():
            if total < queue_per_future:
                queue_per_future = total
            future = executor.submit(process_frames, source_face, target_face, pick_queue(queue, queue_per_future), update)
            futures.append(future)
            total -= queue_per_future
        for future in as_completed(futures):
            future.result()


def create_queue(temp_frame_paths: List[str]) -> Queue[str]:
    queue: Queue[str] = Queue()
    for frame_path in temp_frame_paths:
        queue.put(frame_path)
    return queue


def pick_queue(queue: Queue[str], queue_per_future: int) -> List[str]:
    queues = []
    for _ in range(queue_per_future):
        if not queue.empty():
            queues.append(queue.get())
    return queues


def process_video(source_face: Face, target_face: Face, frame_paths: list[str], process_frames: Callable[[str, List[str], Any], None]) -> None:
    progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
    total = len(frame_paths)
    with tqdm(total=total, desc='İşleme', unit=' kare', dynamic_ncols=True, bar_format=progress_bar_format) as progress:
        multi_process_frame(source_face, target_face, frame_paths, process_frames, lambda: update_progress(progress))


def update_progress(progress: Any = None) -> None:
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / 1024 / 1024 / 1024
    progress.set_postfix({
        'Hafıza Kullanımı': '{:.2f}'.format(memory_usage).zfill(5) + 'GB',
        'İşleme Motoru': swapper.globals.execution_providers,
        'Aktif İş Parçacıkları': swapper.globals.execution_threads
    })
    progress.refresh()
    progress.update(1)
