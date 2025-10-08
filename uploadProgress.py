
import json
import os
import shutil
import sqlite3
import requests
import argparse
from thefuzz import fuzz

# import time, datetime

parser = argparse.ArgumentParser()

parser.add_argument("-H","--host", action='store',help="ABS host, overwrites hardcoded host.")
parser.add_argument("-k","--key", action='store',help="API key, overwrites hardcoded key.")
parser.add_argument("-l","--library", action='store',help="Library ID, overwrites debug library ID.")
parser.add_argument("-u","--useMissing", action='store_true',help="Use missing.json instead of progress.json")
parser.add_argument("-f","--useFuzzyMatching", action='store_true',help="Use fuzzy matching when there is no ASIN/ISBN")
args = parser.parse_args()


# ##### Configuration #####

# Optional hardcoding
ABS_HOST = "http://localhost:13378"
API_KEY = ""
DEBUG_LIBRARY = "0309d2a8-20ff-4ca6-a724-3b8e1831ef40"
LIBRARY_ID = DEBUG_LIBRARY

if args.host:
    ABS_HOST = args.host

if args.key:
    API_KEY = args.key

if args.library:
    LIBRARY_ID = args.library

ME_URI = "/api/me"
SEARCH_URI = f"/api/libraries/{LIBRARY_ID}/search"
BATCH_URI = "/api/me/progress/batch/update"

AUTH = f"?token={API_KEY}"

##### Methods #####

def batchUpload(progs):
    books = []
    for p in progs.values():
        if p["mediaItemType"] != "book":
            continue

        book={"libraryItemId":p["newLibraryItemId"]}
        # book["episodeId"]=p["episodeId"]

        book["isFinished"]=p["isFinished"]
        book["progress"]=p["progress"]
        book["ebookProgress"]=p["ebookProgress"]

        book["currentTime"]=p["currentTime"]
        book["finishedAt"]=p["finishedAt"]
        book["startedAt"]=p["startedAt"]

        book["hideFromContinueListening"]=p["hideFromContinueListening"]
        
        books.append(book)

    req = requests.patch(ABS_HOST+BATCH_URI+AUTH,json=books)

def matchHardPath(path, jBook, qBook):
    keys = path.split("|")
    jVal = jBook
    qVal = qBook

    for key in keys:
        jVal = jVal[key]
        qVal = qVal[key]

    if jVal == qVal:
        return qBook["id"]

    return None

###### Main ######

bookJSON = []
if args.useMissing:
    with open("missing.json","r") as js:
        bookJSON = json.load(js)
        js.close()    
else:
    with open("progress.json","r") as js:
        bookJSON = json.load(js)
        js.close()

foundBooks = {}
missingBooks = []
for jBook in bookJSON:
    skipFuzzyMatch = False
    prog = jBook["progress"]
    prog["newLibraryItemId"] = None
    
    resp = requests.get(ABS_HOST+SEARCH_URI+AUTH+f"&")

    # ### High Confidence match if ASIN or ISBN is present ###

    for k in ["asin","isbn"]:
        val = jBook["media"]["metadata"][k]
        if val != None:
            q = requests.get(ABS_HOST+SEARCH_URI+AUTH+f"&q={val}")
            for qBook in q.json()["book"]:
                prog["newLibraryItemId"] = matchHardPath(f"media|metadata|{k}",jBook,qBook["libraryItem"])
                if prog["newLibraryItemId"] != None:
                    break    

            if prog["newLibraryItemId"] != None:
                print(f"{f"=== Found {jBook["media"]["metadata"]["title"]} ===":^60}")
                foundBooks[prog["newLibraryItemId"]] = prog
                skipFuzzyMatch = True
                break
    
    if skipFuzzyMatch:
        continue

    if not args.useFuzzyMatching:
        print(f"{f"=== Missing {jBook["media"]["metadata"]["title"]} ===":^60}")
        missingBooks.append(prog)
        continue


    ### Fuzzy Matching ###

    title = jBook["media"]["metadata"]["title"]
    series = jBook["media"]["metadata"]["series"] #array of id,name,sequence

    queriesLikelyToHit = [title]
    for s in series:
        queriesLikelyToHit.append(s["name"])


    # People data dont show the books they're associated with
    # for a in authors:
    #     queriesLikelyToHit.append(a["name"])

    # for n in narrators:
    #     queriesLikelyToHit.append(n)

    # Chapter titles and Publication Years arent searched
    # Publisher isnt searched
    # Descriptions also arent searched 
    

    matchData = {}
    for q in queriesLikelyToHit:
        resp = requests.get(ABS_HOST+SEARCH_URI+AUTH+f"&q={q}")
        print(f"                          === Searching {q} ===")
        print()
        hits = []
        for k in resp.json()["book"]:
            hits.append(k["libraryItem"])
        
        for s in resp.json()["series"]:
            hits += s["books"]


        for b in hits:
            newBookId = b["id"]
            if newBookId in matchData:
                matchData[newBookId]["count"] += 1
            else:
                matchData[newBookId] = b
                matchData[newBookId]["count"] = 1
    
    # Sort list of matching IDs by how often they showed up (presumably the most overlap would be the book we're after)
    matchList = []
    for m in matchData:
        matchList.append({"id":m,"count":matchData[m]["count"]})
    matchList = sorted(matchList,key=lambda kv: kv["count"], reverse=True)

    matchScores = []
    for mk in matchList:
        m = matchData[mk["id"]]
        if m["mediaType"] != jBook["mediaType"]:
            continue

        report = {"id":mk["id"]}
        report["title"] = fuzz.ratio(m["media"]["metadata"]["title"], jBook["media"]["metadata"]["title"])
        report["title_set"] = fuzz.token_set_ratio(m["media"]["metadata"]["title"], jBook["media"]["metadata"]["title"])
        report["title_sub_swap"] = fuzz.token_set_ratio(m["media"]["metadata"]["subtitle"], jBook["media"]["metadata"]["title"])
        # report["sub_swap_string"] = f"{m["media"]["metadata"]["subtitle"]}|{jBook["media"]["metadata"]["title"]}"

        report["pub_year_diff"] = -1000
        if m["media"]["metadata"]["publishedYear"] != None and jBook["media"]["metadata"]["publishedYear"] != None:
            report["pub_year_diff"] = -abs(int(jBook["media"]["metadata"]["publishedYear"])-int(m["media"]["metadata"]["publishedYear"]))

        # Books found through the series section dont have authors populated
        # Instead must fingerprint on narrators, publishedYear, publisher
        report["narrators"] = []
        for n in m["media"]["metadata"]["narrators"]:
            record = {"name":n, "best":0}
            for jn in jBook["media"]["metadata"]["narrators"]:
                score = fuzz.token_set_ratio(n, jn)
                if score>record["best"]:
                    record["best"] = score
            report["narrators"].append(record)

        report["authors"] = []
        for n in m["media"]["metadata"]["authors"]:
            record = {"name":n["name"], "best":0}
            for jn in jBook["media"]["metadata"]["authors"]:
                score = fuzz.token_set_ratio(n["name"], jn["name"])
                if score>record["best"]:
                    record["best"] = score
            report["authors"].append(record)
        
        matchScores.append(report)
    

    sortedScores = sorted(matchScores, key=lambda x: (x["title"], x["title_set"], x["pub_year_diff"]), reverse=True)
    
    for r in sortedScores:
        if len(r["authors"]) > 0:
            aveAuth = sum([x["best"] for x in r["authors"]]) / len(r["authors"])
            if aveAuth >= 85:
                # Probably authors match but are missing abreviations or titles
                prog["newLibraryItemId"] = r["id"]
                break
        
        if len(r["narrators"]) > 0:
            aveNarr = sum([x["best"] for x in r["narrators"]]) / len(r["narrators"])
            if aveNarr >= 85:
                # Probably narrators match but are missing abreviations or titles
                prog["newLibraryItemId"] = r["id"]
                break

    if prog["newLibraryItemId"] != None:
        if prog["newLibraryItemId"] not in foundBooks:
            foundBooks[prog["newLibraryItemId"]] = prog
        else:
            missingBooks.append(prog)
            missingBooks.append(foundBooks[prog["newLibraryItemId"]])
            del foundBooks[prog["newLibraryItemId"]]
        continue
    else:
        missingBooks.append(prog)

batchUpload(foundBooks)

# Convert prog objects back into full book progresses for later reprocessing
missingIDs = [x["libraryItemId"] for x in missingBooks]
missingProgs = [x for x in bookJSON if x["id"] in missingIDs]

with open("missing.json","w") as miss:
    miss.write(json.dumps(missingProgs))
    miss.close()
