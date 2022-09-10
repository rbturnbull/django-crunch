================
Datasets
================

Datasets can be in one of four categories.

- Completed: If they have a Status at stage 'UPLOAD' and state 'SUCCESS'.
- Unprocessed: If they are not complete and they are not locked.
- Failed: If they are not complete and unlocked and the latest status has a state of 'FAILED'.
- Running: If they are not complete and unlocked and the latest status is not 'FAILED'.

Querysets for all datasts in these four categories can be obtained by class methods:
Dataset.completed(), Dataset.unprossed(), Dataset.failed(), Dataset.running().

