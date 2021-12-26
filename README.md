# django-eremaea2

[![Build Status](https://github.com/matwey/django-eremaea2/actions/workflows/django.yml/badge.svg)](https://github.com/matwey/django-eremaea2/actions/workflows/django.yml)
[![PyPI version](https://badge.fury.io/py/django-eremaea2.svg)](https://badge.fury.io/py/django-eremaea2)

django-eremaea2 is a simple [Django] application to store and manage webcam image snapshots.
The application is built on top of [django-rest-framework] and provides REST API to access the files.

There are three kind of resources available through REST API interface.
A *collection* is a collection of *snapshots*.
A *snapshot* is image file in essence.
For any *snapshot* there is a *retention policy* associated with to specify how long store the file.

## Installation

The following prerequisites are required to operate django-eremaea2:
* [django-rest-framework] - powerful and flexible toolkit that makes it easy to build Web APIs.
* [dj-inmemorystorage] - a non-persistent in-memory data storage backend for Django (required for testing).

To use django-eremaea2 in your django project, include the following code into your ```settings.py```:
```
INSTALLED_APPS = (
     #...
    'rest_framework',
    'eremaea',
)
```

Into your ```urls.py``` you have to add the following:
```
urlpatterns = patterns('',
    #...
    url(r'^eremaea/', include('eremaea.urls')),
)
```

## Configuration
The whole configuration is stored into the project database, there is not separate dedicated config file.

The ```RetentionPolicy``` model has two parameters: a lookup field ```name``` and ```duration``` that specifies time-to-live for associated objects.
To perform actual cleanup a POST request to the endpoint ```http://example.com/eremaea/retention_policies/{name}/purge``` is required.
The ```Collection``` model has two parameters: a lookup field ```name``` and ```default_retention_policy```.
The ```Snapshot``` model has the following field: associated ```collection``` and ```retention_policy```, ```file``` object, and auto-now ```date```.
New images are uploaded by POST request to the endpoint ```http://example.com/eremaea/snapshots/?collection=collection_name&retention_policy=retention_policy_name```.
The latest query parameter is optional one.

The other ways to configure the application are Django fixtures, Django admin interface, [django-rest-framework] web browsable interface, and REST API itself.

## Authentication and permissions
You may utilise all possible options provided by [django-rest-framework]. See [Tutorial](http://www.django-rest-framework.org/tutorial/4-authentication-and-permissions/) for reference.

## Caching
You may utilise all caching mechanisms provided by [Django] framework. See [Django's cache framework](https://docs.djangoproject.com/en/dev/topics/cache/).

## Feedback
If you have any questions, issues, or pull-requests, you are welcome to use GitHub infrastructure.

## License

Copyright (c) 2016, Matwey V. Kornilov

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


[Django]:https://www.djangoproject.com/
[django-rest-framework]:http://www.django-rest-framework.org
[dj-inmemorystorage]:https://pypi.python.org/pypi/dj-inmemorystorage
