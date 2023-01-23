================================================================
django-crunch
================================================================

.. image:: https://raw.githubusercontent.com/rbturnbull/django-crunch/main/docs/images/crunch-banner.svg

.. start-badges

|testing badge| |coverage badge| |docs badge| |black badge|

.. |testing badge| image:: https://github.com/rbturnbull/django-crunch/actions/workflows/testing.yml/badge.svg
    :target: https://github.com/rbturnbull/django-crunch/actions

.. |docs badge| image:: https://github.com/rbturnbull/django-crunch/actions/workflows/docs.yml/badge.svg
    :target: https://rbturnbull.github.io/django-crunch
    
.. |black badge| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    
.. |coverage badge| image:: https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/rbturnbull/d83b00666fad82df59a814083a09d1c1/raw/coverage-badge.json
    :target: https://rbturnbull.github.io/django-crunch/coverage/
    
.. end-badges


.. start-quickstart

A data processing orcestration tool.
Crunch allows you to visualize the datasets, orchestrate and manage the processing online and present the results to the world.

Description
===========

Crunch coordinates three components. First there is a web application in the cloud. 
Crunch includes a Django app which can be included in a website built using the Django framework for building database driven websites. 
The website allows users to create what we call ``datasets``. 
Each dataset corresponds to one collection of files and metadata which is designed to be run through the workflow. 
Each dataset has its own page on the website which displays all the information about it.

The second component is data storage. 
The main use-case for crunch is when your datasets are so many and so large that you cannott fit them all on to the disk where you are doing your computation. 
With crunch, the data can be stored in any of the media storage options available with Django. 
These can be Amazon S3, Google Cloud or many other storage options. 

The third component is the client which runs at the place where you are performing the computation. 
This could be in a high-performance computing environment, or it could be on a virtual machine in the cloud or it could be just on your own laptop. 
The user just runs the crunch command line tool. 
The command line tool communicates with the website to find out which dataset should be processed next, 
then it copies it from storage and saves it locally. 
Then it processes the dataset using a pre-defined workflow provided by the user. 
When it is finished, it copies back the data to the storage with the resulting files. 
At each stage the user can see the status on the website interface. 
If you run the `crunch loop`` command then the client continually loops through the datasets until they are completely finished. 
You can run as many clients in parallel as you have computing resources.

Once each dataset is processed, the resulting files can be accessed via the website. 
The permissions for the website can be set dynamically so that users can restrict access 
to just the team for while the data is being processed and once the results are ready for the world then you can allow access to the public.


Installation
==================================

The crunch app for a Django website and the command-line client are installed with pip:

.. code-block:: bash

    pip install git+https://github.com/rbturnbull/django-crunch


Install the crunch app to the Djanco website project by adding it to the settings:

.. code-block:: python

    INSTALLED_APPS += [
        "crunch",
    ]

Then add the urls to your main urls.py:

.. code-block:: python

    urlpatterns += [
        path('crunch/', include('crunch.django.app.urls'))),    
    ]

The path ``crunch/`` can be changed to be whatever you choose.

Usage
==================================

Create projects, datasets, items and attributes on the website using the HTML interface, the crunch command-line client or the Python API.

Upload initial data for each dataset as needed to the storage using the Crunch HTML interface or direct to the folder for each dataset on the storage.

Then process each dataset at the location where you are performing your compute with the crunch client. All datasets can be processed with the single command:

.. code-block:: bash

    crunch loop

.. end-quickstart

Credits
==================================

.. start-credits

Robert Turnbull, Mar Quiroga and Simon Mutch from the Melbourne Data Analytics Platform.

Publication and citation details to follow.

.. end-credits
