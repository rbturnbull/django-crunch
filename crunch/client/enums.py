from enum import Enum




class RunResult(Enum):
    SUCCESS = 0
    FAIL = 1

    def __bool__(self):
        return self.value > 0
