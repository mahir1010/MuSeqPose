from abc import ABC, abstractmethod

import numpy as np

from Skeleton import Skeleton,Part


class DataStoreInterface(ABC):

    def __init__(self,body_parts):
        self.body_parts=body_parts

    @abstractmethod
    def get_skeleton(self, index) -> Skeleton:
        pass

    @abstractmethod
    def set_skeleton(self, index, skeleton:Skeleton) -> None:
        pass

    @abstractmethod
    def set_behaviour(self, index, activity: str) -> None:
        pass

    @abstractmethod
    def get_behaviour(self, index) -> str:
        pass

    @abstractmethod
    def save_file(self, path: str) -> None:
        pass

    @abstractmethod
    def get_keypoint_slice(self, slice_indices: list, name: str) -> np.ndarray:
        pass

    @abstractmethod
    def set_keypoint_slice(self, slice_indices: list, name: str, data: np.ndarray) -> None:
        pass

    @abstractmethod
    def row_iterator(self) -> Skeleton:
        pass

    @abstractmethod
    def get_marker(self, index,name) -> Part:
        pass

    @abstractmethod
    def set_marker(self, index, part: Part) -> None:
        pass

    @abstractmethod
    def build_skeleton(self,row) -> Skeleton:
        pass