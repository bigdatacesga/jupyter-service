Jupyter REST API
================

Introduction
------------
Allows to launch Jupyter servers on-demand.

Installation
------------

    virtualenv venv
    . venv/bin/activate
    pip install -r requirements.txt
    python wsgi.py


Test with:

```
curl -X POST http://127.0.0.1:6004/jupyter/api/v1/servers
----
http POST http://127.0.0.1:6004/jupyter/api/v1/servers
```

