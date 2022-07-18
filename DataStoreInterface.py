from abc import ABC, abstractmethod

import numpy as np

from Keypoint import Keypoint


class DataStoreInterface(ABC):

    @abstractmethod
    def get_keypoint_location(self, keypoint: Keypoint, index) -> Keypoint:
        pass

    @abstractmethod
    def set_keypoint_location(self, keypoint: Keypoint, index) -> Keypoint:
        pass
    @abstractmethod
    def set_activity(self,activity: str,index) -> None:
        pass
    @abstractmethod
    def get_activity(self,index) -> str:
        pass
    @abstractmethod
    def save_file(self, path: str) -> None:
        pass

    @abstractmethod
    def get_keypoint_slice(self, name: str, slice_indices: list) -> np.ndarray:
        pass

    @abstractmethod
    def set_keypoint_slice(self, name: str, slice_indices: list, data: np.ndarray) -> None:
        pass
