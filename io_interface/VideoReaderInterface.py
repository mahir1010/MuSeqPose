from abc import ABC, abstractmethod

import numpy as np


class VideoReaderInterface(ABC):

    def __init__(self, name, video_path, fps):
        self.name = name
        self.video_path = video_path
        self.fps = fps

    @abstractmethod
    def seek_pos(self, index: int) -> None:
        pass

    @abstractmethod
    def next_frame(self) -> np.ndarray:
        pass

    @abstractmethod
    def get_current_index(self) -> int:
        pass

    @abstractmethod
    def release(self) -> None:
        pass

    @abstractmethod
    def pause(self) -> None:
        pass

    @abstractmethod
    def get_number_of_frames(self) -> int:
        pass
