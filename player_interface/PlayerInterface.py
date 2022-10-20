from abc import ABC, abstractmethod

from config import MuSeqPoseConfig


class PlayerInterface(ABC):

    def __init__(self, config:MuSeqPoseConfig, view_data):
        self.config = config
        self.view_data = view_data
        self.data_store = None
        self.frame_number = 0
        self.is_video_playing = False
        self.data_point = None

    @abstractmethod
    def render_next_frame(self, image_viewer):
        pass

    @abstractmethod
    def render_previous_frame(self):
        pass

    @abstractmethod
    def seek(self, frame_number):
        pass

    @abstractmethod
    def get_number_of_frames(self):
        pass

    @abstractmethod
    def release(self):
        pass
