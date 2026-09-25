class Range:
    """
    Represents a range of values to perform grid search over
    """
    def __init__(self, min: int, max: int, step: int):
        self.min = min
        self.max = max
        self.step = step
