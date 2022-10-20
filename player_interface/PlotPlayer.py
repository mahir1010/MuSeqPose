import os
from abc import ABC

import numpy as np
from vispy.scene import SceneCanvas, cameras, XYZAxis, Plane
from vispy.scene.visuals import LinePlot, Box
from vispy.visuals.transforms import STTransform

from OptiPose.data_store_interface import initialize_datastore_reader
from config import PlotConfig, MuSeqPoseConfig, ReconstructionPlotConfig
from player_interface.PlayerInterface import PlayerInterface


def get_visual(data):
    visual = None
    scale = [1, 1, 1]
    translate = [0, 0, 0]
    if data['type'] == "XYZAxis":
        visual = XYZAxis()
    elif data['type'] == "Plane":
        visual = Plane(color=data.get('color', (0.8, 0, 0)), width=data.get('width', 1), height=data.get('height', 1))
        translate = data.get('translate', translate).copy()
        translate[0] += data.get('width', 1) / 2
        translate[1] += data.get('height', 1) / 2
    elif data['type'] == "Box":
        visual = Box(width=data.get('width', 1), height=data.get('height', 1), depth=data.get('depth', 1),
                     color=data.get('color', (0.8, 0, 0)))
        translate = data.get('translate', translate).copy()
        translate[0] += data.get('width', 1) / 2
        translate[1] += data.get('depth', 1) / 2
        translate[2] += data.get('height', 1) / 2
    if visual:
        visual.transform = STTransform(scale=data.get('scale', scale), translate=translate)
    return visual


class PlotPlayer(PlayerInterface, ABC):
    def render_previous_frame(self):
        self.frame_number = max(0, self.frame_number - 1)

    def seek(self, frame_number):
        self.frame_number = max(0, frame_number)

    def get_number_of_frames(self):
        return len(self.data_store)

    def __init__(self, config:MuSeqPoseConfig, view_data:PlotConfig):
        super(PlotPlayer, self).__init__(config, view_data)
        columns = view_data.annotation_columns
        path = os.path.join(config.output_folder, view_data.annotation_file)
        self.data_store = initialize_datastore_reader(columns, path, view_data.annotation_file_flavor)
        self.scene_canvas = None

    def get_widget(self):
        return self.scene_canvas.native


class ReconstructionPlayer(PlotPlayer):
    def release(self):
        if self.scene_canvas is not None:
            self.scene_canvas.close()

    def __init__(self, config:MuSeqPoseConfig, view_data:ReconstructionPlotConfig):
        super(ReconstructionPlayer, self).__init__(config, view_data)
        size = view_data.size
        self.max_limits = view_data.normalization_max_limit
        self.min_limits = view_data.normalization_min_limit
        self.threshold = self.config.threshold
        self.scene_canvas = SceneCanvas(size=size)
        self.scene_canvas.unfreeze()
        view = self.scene_canvas.central_widget.add_view()
        view.camera = cameras.TurntableCamera(elevation=40, fov=30, distance=1)
        view.camera.center = (0.5, 0.5, 0)
        self.markers = {}
        self.lines = []
        self.line = LinePlot(np.zeros((self.config.num_parts, 3)), width=2, color='red', parent=view.scene,
                             connect=np.array([[0, 1]]), marker_size=4)
        self.scene_canvas.freeze()
        for item in view_data.environment.values():
            view.add(get_visual(item))
        self.scene_canvas.create_native()

    def render_next_frame(self, image_viewer):
        skeleton = self.data_store.get_skeleton(self.frame_number).normalize(self.max_limits, self.min_limits)
        self.frame_number += 1
        points = [skeleton[p] for p in skeleton.body_parts_map.keys() if skeleton[p] >= self.threshold]
        point_map = {p.name: i for i, p in enumerate(points)}
        connections = []
        for idx, end_points in enumerate(self.config.skeleton):
            if skeleton[end_points[0]] >= self.threshold and skeleton[end_points[1]] >= self.threshold:
                connection = [point_map[end_points[0]], point_map[end_points[1]]]
                connections.append(connection)
        if len(connections) and len(points):
            self.line.set_data(np.array(points), connect=np.array(connections))
            self.line.visible = True
        else:
            self.line.visible = False
