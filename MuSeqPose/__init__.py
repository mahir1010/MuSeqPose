from importlib.resources import files, as_file

from PySide2.QtCore import QByteArray

import MuSeqPose.Resources
import MuSeqPose.Resources.icons
from PySide2.QtGui import QImage, QIcon, QColor, QPainter, QPixmap, Qt
from PySide2.QtSvg import QSvgRenderer

def get_resource(name):
    with as_file(files(MuSeqPose.Resources).joinpath(name)) as file:
        return str(file)


def get_icon(name,size=(32,32),color=(255,255,255)):
    with as_file(files(MuSeqPose.Resources.icons).joinpath(name)) as file:
        color = QColor(*color)
        color_str = color.name()
        svg_data = open(str(file),'r').read()
        svg_data = svg_data.replace('#FFFFFF',color_str)
        image = QImage(*size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        renderer = QSvgRenderer(QByteArray(svg_data.encode()))
        renderer.render(QPainter(image))
        return QIcon(QPixmap.fromImage(image))
