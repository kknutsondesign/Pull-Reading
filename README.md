# Pull-Reading

## progresses.py
<pre>
usage: progresses.py [-h] [-H HOST] [-k KEY] [-p] [-t]

options:
-  -H, --host HOST_URL  ABS host, overwrites hardcoded host.
-  -k, --key API_KEY    API key, overwrites hardcoded key.
-  -p, --pull           Pull new reading history to overwrite existing progress.json.
-  -t, --test           Run script but do not do any file manipulation.
</pre>

## uploadProgress.py
<pre>
usage: uploadProgress.py [-h] [-H HOST] [-k KEY] [-l LIBRARY] [-u]

options:
-  -H, --host HOST_URL        ABS host, overwrites hardcoded host.
-  -k, --key API_KEY          API key, overwrites hardcoded key.
-  -l, --library LIBRARY_ID   Library ID, overwrites debug library ID.
-  -u, --useMissing           Use missing.json instead of progress.json
-  -f, --useFuzzyMatching     Use fuzzy matching when there is no ASIN/ISBN
</pre>
## Goodreads
Using progresses.py will save your reading history as .json but also output a CSV compatible with Goodreads book importing