=================
Storage
=================

Django uses an abstract `file storage class <https://docs.djangoproject.com/en/4.1/ref/files/storage/>`_. 
to connect to different kinds of data storage options.

The widely used `django-storages <https://django-storages.readthedocs.io/en/latest/>`_ app allows you to use one of the following storage backends:

- Amazon S3
- Apache Libcloud
- Azure Storage
- Backblaze B2
- Digital Ocean
- Dropbox
- FTP
- Google Cloud Storage
- SFTP

Other plugins are available for other types of storage or you can write your own custom class using the Django reference for your system.

Whatever storage system you use will need to be specified in the settings for the cloud server 
and these values must be available in a TOML file or JSON file when running the client to perform the computation. For more information, see the section on :ref:`Environment Variables`.

