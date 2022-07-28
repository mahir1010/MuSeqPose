from glob import glob
import os

import numpy as np

from io_interface.VideoReaderInterface import VideoReaderInterface
import cv2

class ImageSequenceReader(VideoReaderInterface):

    def seek_pos(self, index: int) -> None:
        self.frame_number = index-1

    def next_frame(self) -> np.ndarray:
        self.frame_number+=1
        return cv2.cvtColor(cv2.imread(self.images[self.frame_number]),cv2.COLOR_BGR2RGB)

    def get_current_index(self) -> int:
        return self.frame_number

    def release(self) -> None:
        pass

    def pause(self) -> None:
        pass

    def get_number_of_frames(self) -> int:
        return len(self.images)

    def __init__(self ,name, video_path, fps,file_formats=['[jJ][pP][gG]', '[pP][nN][gG]','[bB][mM][pP]']):
        super(ImageSequenceReader, self).__init__(name,video_path,fps)
        self.images=[]
        for file_format in file_formats:
            self.images.extend(glob(os.path.join(video_path, '*.{}'.format(file_format))))
        self.images.sort()
        self.frame_number=0
