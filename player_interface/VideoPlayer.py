from OptiPose import AnnotationConfig
from OptiPose.data_store_interface import initialize_datastore_reader
from OptiPose.video_reader_interface import initialize_video_reader
from config import MuSeqPoseConfig
from player_interface.PlayerInterface import PlayerInterface


class VideoPlayer(PlayerInterface):

    def release(self):
        self.video_reader.release()

    def __init__(self, config: MuSeqPoseConfig, view_data: AnnotationConfig):
        super(VideoPlayer, self).__init__(config, view_data)
        self.video_reader = initialize_video_reader(view_data.video_file, config.framerate, view_data.video_reader)
        self.data_store = initialize_datastore_reader(config.body_parts, view_data.annotation_file,
                                                      view_data.annotation_file_flavor)
        self.current_frame = None

    def render_next_frame(self, image_viewer):
        frame = self.video_reader.next_frame()
        if frame is not None:
            if self.data_point is not None:
                self.data_store.set_skeleton(self.frame_number, self.data_point)
            self.frame_number = self.video_reader.get_current_index()
            self.data_point = self.data_store.get_skeleton(self.frame_number)
            image_viewer.draw_frame(frame)
            self.current_frame = frame
        return self.frame_number

    def render_previous_frame(self):
        if self.frame_number != 0:
            self.seek(self.frame_number - 1)

    def seek(self, frame_number):
        self.video_reader.seek_pos(max(0, frame_number))

    def get_number_of_frames(self):
        return self.video_reader.get_number_of_frames()
