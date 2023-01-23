=========
Compute
=========

On the computational infrastructure, install django-crunch so you can use the crunch client.


Environment Variables
=====================

The crunch client needs to know how to access both the cloud server and the data storarage. 
These can be set with the following environment variables:

- ``CRUNCH_URL`` 
    The URL to the cloud server. 
    This can also be set with the command-line option ``--url URL``.
- ``CRUNCH_TOKEN``
    The access token for a user on the cloud server. 
    This can be found in the admin section of the cloud server. 
    This variable can also be given to the client with the command-line option ``--token TOKEN``.
- ``CRUNCH_STORAGE_SETTINGS``
    The path to a file with the parameters needed to instantiate the Django file storage class just as it is found on the cloud server. 
    This file can be in TOML format or JSON. 
    The values should be the same as what is in the cloud server Django settings.
    This variable can also be given to the client with the command-line option ``--storage-settings PATH/TO/SETTINGS``.

If any of these aren't provided as either command-line options or as environment variables, the client will prompt for the values.

Client Commands
===============

To process a particular dataset, you can use the following command:

.. code-block:: bash

    crunch run DATASET-SLUG

To simply process the next dataset on the cloud server:

.. code-block:: bash

    crunch next

To process the next dataset for a specific project:

.. code-block:: bash

    crunch next --project PROJECT-SLUG

To process all the remaining datasets on the cloud server:

.. code-block:: bash

    crunch loop

To process all the remaining datasets for a particular project:

.. code-block:: bash

    crunch loop --project PROJECT-SLUG

Other command line options are available. Check the command-line reference in the documentation or read the crunch client help listings. e.g.

.. code-block:: bash

    crunch --help


Stages
==========

Processing a dataset goes through 3 stages: Setup, Workflow and Upload. 
Each of these stages will send status updates to the cloud server. 
The status updates are for one of the following three states: Start, Success or Fail.
A typical successful processing run for a dataset will send 6 status updates: Setup Start, Setup Success, Workflow Start, Workflow Success, Upload Start, Upload Success.
If any of the stages fail, then a ``Fail`` status will be sent and the processing job will stop.

Setup
--------

This involves:

- Copying the initial data from storage
- Saving the MD5 checksums for all the initial data in ``.crunch/setup_md5_checksums.json``
- Saves the metadata for the dataset in ``.crunch/dataset.json``
- Saves the metadata for the project in ``.crunch/project.json``
- Creates the script to run the workflow (either a bash script or a Snakefile for Snakemake)

Workflow
------------

Runs the workflow on a dataset that has been set up.

This involves running a bash script as a subprocess or running Snakemake with a Snakefile.


Upload
------------
        
Uploads new or modified files to the storage for the dataset.

It also creates the following files:
- ``.crunch/upload_md5_checksums.json`` which lists all MD5 checksums after the dataset has finished.
- ``.crunch/deleted.txt`` which lists all files that were present after setup but which were deleted as the workflow ran.

.. note::

    Currently crunch does not delete files from the remote storage if they were deleted during the workflow. 
    The files are just listed in ``.crunch/deleted.txt``

.. warning::

    The Django storage class being used may not overwrite modified files but instead change the names slightly. 
    For this reason, it's best not to modify files in the workflow section but create new files instead.
    This behaviour may change in future versions of crunch.
