================
Cloud
================

Items
================


Projects
================


Datasets
================

Categories
----------

Datasets can be in one of four categories.

- **Completed**: If they have a Status at stage ``UPLOAD`` and state ``SUCCESS``.
- **Unprocessed**: If they are not complete and they are not locked.
- **Failed**: If they are not complete and unlocked and the latest status has a state of ``FAILED``.
- **Running**: If they are not complete and unlocked and the latest status is not ``FAILED``.

Querysets for all datasts in these four categories can be obtained by class methods:
``Dataset.completed()``, ``Dataset.unprocessed()``, ``Dataset.failed()``, ``Dataset.running()``.


Status
================


Attributes
================

Attributes are a way of adding metadata to items. There are several different kinds of attributes:

- **CharAttribute**: An attribute for storing metadata as a string (of maximum length 1023 characters).
- **FloatAttribute**:
- **IntegerAttribute**:
- **FilesizeAttribute**:
- **BooleanAttribute**: 
- **DateTimeAttribute**:
- **DateAttribute**:
- **URLAttribute**:
- **LatLongAttribute**: An attribute for storing a geolocation (in decimal degrees).