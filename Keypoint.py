class Keypoint:

    def __init__(self, name, color: list):
        self.name = name
        self.x_loc = -1
        self.y_loc = -1
        self.likelihood = 0
        self.color = color
        self.visible = True

    def set_location(self, x, y):
        self.x_loc, self.y_loc = x, y

    def get_location(self):
        return self.x_loc, self.y_loc

    def set_likelihood(self, likelihood):
        self.likelihood = likelihood

    def set_visible(self, is_visible):
        self.visible = is_visible

    def get_likelihood(self):
        return self.likelihood

    def __lt__(self, other):
        return self.likelihood < other

    def __le__(self, other):
        return self.likelihood <= other

    def __ge__(self, other):
        return self.likelihood >= other

    def __gt__(self, other):
        return self.likelihood > other

    def __str__(self):
        return f'{self.name} : [{self.x_loc},{self.y_loc}] ({self.likelihood})'
