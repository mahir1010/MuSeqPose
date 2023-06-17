import os
from abc import ABC

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from vispy.scene import SceneCanvas, cameras, XYZAxis, Plane
from vispy.scene.visuals import LinePlot, Box
from vispy.visuals.filters.mesh import ShadingFilter
from vispy.visuals.transforms import STTransform

from MuSeqPose.config import PlotConfig, ReconstructionPlotConfig, LinePlotConfig
from MuSeqPose.player_interface.PlayerInterface import PlayerInterface
from MuSeqPose.utils.session_manager import SessionManager
from cvkit.pose_estimation.data_readers import initialize_datastore_reader
from cvkit.pose_estimation.utils import get_spherical_coordinates


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
        visual._mesh.shading_filter = ShadingFilter(shading='smooth', ambient_light=(1, 1, 1, 0.55),
                                                    diffuse_light=(1, 1, 1, 0.7), specular_light=(1, 1, 1, 0.35))
        visual._mesh.attach(visual._mesh.shading_filter)
        visual._mesh.shading = 'smooth'
        translate = data.get('translate', translate).copy()
        translate[0] += data.get('width', 1) / 2
        translate[1] += data.get('depth', 1) / 2
        translate[2] += data.get('height', 1) / 2
    if visual:
        visual.transform = STTransform(scale=data.get('scale', scale), translate=translate)
    return visual


class PlotPlayer(PlayerInterface, ABC):
    def release(self):
        if self.scene_canvas is not None:
            self.scene_canvas.close()

    def render_previous_frame(self):
        self.frame_number = max(0, self.frame_number - 1)

    def seek(self, frame_number):
        self.frame_number = max(0, frame_number)

    def get_number_of_frames(self):
        return len(self.data_store)

    def __init__(self, session_manager: SessionManager, view_name, view_data: PlotConfig):
        super(PlotPlayer, self).__init__(session_manager, view_name, view_data)
        columns = view_data.annotation_columns if view_data.annotation_columns is not None else self.config.body_parts
        path = os.path.join(self.config.output_folder, view_data.annotation_file)
        self.data_store = initialize_datastore_reader(columns, path, view_data.annotation_file_flavor)
        self.scene_canvas = None

    def get_widget(self):
        return self.scene_canvas.native


class LinePlotPlayer(PlotPlayer):
    def get_widget(self):
        return self.scene_canvas

    def seek(self, frame_number):
        super(LinePlotPlayer, self).seek(frame_number)
        for key in self.data:
            self.data[key].clear()
        self.axis.set_xlim((self.frame_number, self.frame_number + self.x_width))

    def __init__(self, session_manager: SessionManager, view_name, view_data: LinePlotConfig):
        super(LinePlotPlayer, self).__init__(session_manager, view_name, view_data)
        size = view_data.size
        self.scene_canvas = FigureCanvasQTAgg(Figure())
        self.scene_canvas.setFixedSize(*size)
        self.axis = self.scene_canvas.figure.subplots()
        self.x_width = view_data.normalization_max_limit[0] - view_data.normalization_min_limit[0]
        self.axis.set_ylim([view_data.normalization_min_limit[1], view_data.normalization_max_limit[1]])
        self.data = {}
        self.line_objects = {}
        for line in self.view_data.lines.values():
            self.data[line['data']] = []
            self.line_objects[line['data']], = self.axis.plot(range(0, self.x_width), [0] * self.x_width,
                                                              color=line['color'], label=line['legend'])
        self.scene_canvas.figure.legend()

    def render_next_frame(self, image_viewer):
        skeleton = self.data_store.get_skeleton(self.frame_number)
        self.frame_number += 1
        resize_x = False
        for key in self.data:
            self.data[key].append(get_spherical_coordinates(skeleton[key])[0])
            if len(self.data[key]) > self.x_width:
                self.data[key].pop(0)
                resize_x = True
            self.line_objects[key].set_data(list(range(self.frame_number - len(self.data[key]), self.frame_number)),
                                            self.data[key])
        if resize_x:
            self.axis.set_xlim(self.frame_number + 1 - self.x_width, self.frame_number + 1)
        self.scene_canvas.figure.canvas.draw()


class ReconstructionPlayer(PlotPlayer):

    def __init__(self, session_manager: SessionManager, view_name, view_data: ReconstructionPlotConfig):
        super(ReconstructionPlayer, self).__init__(session_manager, view_name, view_data)
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
        self.line = LinePlot(np.zeros((self.config.num_parts, 3)), width=2, color=view_data.color, parent=view.scene,
                             connect=np.array([[0, 1]]), marker_size=4, symbol='o', edge_width=2, face_color='white')
        self.scene_canvas.freeze()
        for item in view_data.environment.values():
            view.add(get_visual(item))
        self.scene_canvas.create_native()
        self.scene_canvas.native.setFixedSize(*size)

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
