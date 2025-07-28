# Pull-Reading

## progresses.py
usage: progresses.py [-h] [-H HOST] [-k KEY] [-p] [-t]
<pre>
options:
-  -H, --host HOST  ABS host, overwrites hardcoded host.
-  -k, --key KEY    API key, overwrites hardcoded key.
-  -p, --pull       Pull new reading history from the host.
-  -t, --test       Run script but do not do any file manipulation.

## uploadProgress.py
usage: uploadProgress.py [-h] [-H HOST] [-k KEY] [-l LIBRARY] [-u]

options:
-  -H, --host HOST         ABS host, overwrites hardcoded host.
-  -k, --key KEY           API key, overwrites hardcoded key.
-  -l, --library LIBRARY   Library ID, overwrites debug library ID.
-  -u, --useMissing        Whether to use a progress.json or missing.json
</pre>
## Goodreads
Using progresses.py will save your reading history as .json but also output a CSV compatible with Goodreads book importing