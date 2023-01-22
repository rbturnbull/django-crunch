from enum import Enum


class WorkflowType(str, Enum):
    snakemake = "snakemake"
    script = "script"


class RunResult(Enum):
    SUCCESS = 0
    FAIL = 1

    def __bool__(self):
        return self.value > 0
