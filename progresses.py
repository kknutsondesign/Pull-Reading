# Pull all reading progress from the /me endpoint and store as a file
# Look up every item to pull full book data
# Export as Goodreads csv

# TO USE:
# Paste URL to the ABS server in ABS_HOST
# Paste your api key in the API_KEY - Login to website and look for `Authorization: Bearer {your key}` in your browser's network tab
# -H and -k flags overwrite hardcoded values
# -p pulls reading data again even in progress.json exists
# -t runs like normal but does not write any values

import json
import os
import shutil
import sqlite3
import requests
import argparse

# TODO: Options for using db if access is available for different steps

parser = argparse.ArgumentParser()

parser.add_argument("-H","--host", action='store',help="ABS host, overwrites hardcoded host.")
parser.add_argument("-k","--key", action='store',help="API key, overwrites hardcoded key.")
parser.add_argument("-p", "--pull", action='store_true',help="Pull new reading history from the host.")
parser.add_argument("-t", "--test", action='store_true',help="Run script but do not do any file manipulation.")
args = parser.parse_args()

# ##### Configuration #####

ABS_HOST = "http://localhost:13378"
API_KEY = ""

if args.host:
    ABS_HOST = args.host

if args.key:
    API_KEY = args.key

ME_URI = "/api/me"
USER_URI = "/api/user/"
ITEM_URI = "/api/items/"

AUTH = f"token={API_KEY}"
# Some way to do metadata-object path too?

##### Methods #####

def pullProgress():
    print("Pulling progress data")
    me = requests.get(f"{ABS_HOST}{ME_URI}?token={API_KEY}")
    print(me.reason)


    books = []

    for pObject in me.json()["mediaProgress"]:
        book = {}
        book["progress"] = pObject
        books.append(book)

    print("Pulling book info")

    for book in books:
        req = requests.get(f"{ABS_HOST}{ITEM_URI}{book["progress"]["libraryItemId"]}?{AUTH}")
        print(req.reason)
        info = req.json()
        if req.ok:
            book.update(info)

    with open("progress.json","w") as f:
        if not args.test: 
            f.write(json.dumps(books))
        f.close()
    
    print("Done pulling reading history")

## Export Types ##

def goodreadsCSV():
    print("Writing to CSV compatible with GoodReads")
    # Title, Author, Additional Authors(, seperated list), ISBN, Publisher, Binding?(Audiobook), Year Published, Bookshelves, Bookshelves with positions? (Collections)
    books = []

    with open("progress.json","r") as js:
        books = json.load(js)
        js.close()
    
    with open("toGoodreads.csv","w") as csv:
        headers = ["Title", "Author", "Additional Authors", "ISBN", "Publisher", "Year Published", "Binding"]

        if not args.test:
            csv.writelines(','.join(f'"{w}"' for w in headers)+'\n')
        
        for b in books:
            
            Title = ""
            Authors = []
            Narrators = []
            ISBN = ""
            Publisher = ""
            Published = ""
            Binding = ""
            Tags = ""

            Title = b["media"]["metadata"]["title"]
            for a in b["media"]["metadata"]["authors"]:
                Authors.append(a["name"])
            
            Narrators = b["media"]["metadata"]["narrators"]
            ISBN = b["media"]["metadata"]["isbn"]
            Publisher = b["media"]["metadata"]["publisher"]
            Published = b["media"]["metadata"]["publishedYear"]
            Binding = "Audiobook" if b["progress"]["progress"] != 0 and b["progress"]["ebookProgress"] == 0 else ""

            values = []
            values.append(Title)
            values.append(Authors[0])
            values.append(f"{','.join(Authors[1:]+Narrators)}")
            values.append(ISBN)
            values.append(Publisher)
            values.append(Published)
            values.append(Binding)

            if not args.test:
                csv.writelines(','.join(f'"{v.replace('"',"'") if v else ""}"' for v in values)+"\n")

        csv.close()

if args.pull or not os.path.isfile("progress.json"):
    pullProgress()

goodreadsCSV()