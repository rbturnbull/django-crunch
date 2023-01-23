================
Cloud Server
================

The database on the cloud server includes the following types of Django models.

Items
================

A general class of object which can be placed in a hierachical tree. 

Each item can be viewed online with a details page and each item can be given any number of attributes to store metadata.

The most important types of items are Projects and Datasets.

Projects
================

An item which collects a number of datasets which should be run with the same workflow.

Projects ought not to have parents in the tree structure of items.

Datasets can have any number of items as decendants.

Datasets
================

An item should be run once in a workflow.

The parent of a dataset should be its project.

Categories
----------

Datasets can be in one of four categories.

- **Completed**: If they have a :ref:`Status` at stage ``UPLOAD`` and state ``SUCCESS``.
- **Unprocessed**: If they are not complete and they are not locked.
- **Failed**: If they are not complete and unlocked and the latest status has a state of ``FAILED``.
- **Running**: If they are not complete and unlocked and the latest status is not ``FAILED``.

Querysets for all datasts in these four categories can be obtained by class methods:
``Dataset.completed()``, ``Dataset.unprocessed()``, ``Dataset.failed()``, ``Dataset.running()``.


Status
================

The result of an action at one stage in the workflow. For more information, see the documetation about the computational :ref:`Stages`.

Attributes
================

Attributes are a way of adding metadata to items (including Projects and Datasets). There are several different kinds of attributes:

- **CharAttribute**: An attribute for storing metadata as a string (of maximum length 1023 characters).
- **FloatAttribute**:
- **IntegerAttribute**:
- **FilesizeAttribute**:
- **BooleanAttribute**: 
- **DateTimeAttribute**:
- **DateAttribute**:
- **URLAttribute**:
- **LatLongAttribute**: An attribute for storing a geolocation (in decimal degrees).