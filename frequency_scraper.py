from requests_html import HTMLSession
from bs4 import BeautifulSoup
import re
import sqlite3
import sys
import time

SEARCH_PREFIX = "https://www.google.com/search?q="

satnames = ["GOES", "BEIDOU", "STARLINK"]

keywords = ["MHz", "GHz", "hertz"]

keytags = ["b", "td", "em"]

replace_items = {
        "hertz" : "Hz",
        "giga" : "G",
        "mega" : "M"
        }

#temporary string replacements so the 
#alphabet filter doesn't remove things like
#GHz and MHz
alpha_replace_saves = {
        "MHz" : "<6>",
        "GHz" : "<9>"
        }

def removeChar(char):
    if char != "." and char.isalpha():
        return True
    if char == "(" or char == ")":
        return True
    return False

def processTagText(text):
    for key in replace_items.keys():
        text = text.replace(key, replace_items[key])
        text = text.replace(key.upper(), replace_items[key])
        text = text.replace(key.lower(), replace_items[key])

    text = text.replace("plus or minus", "$")
    text = text.replace("+/-", "$")
    text = text.replace("-", ">") #dash
    text = text.replace("–", ">") #en dash
    text = text.replace("—", ">") #em dash
    text = text.replace("to", ">")

    for r in alpha_replace_saves:
        text = text.replace(r, alpha_replace_saves[r])

    for char in text:
        if removeChar(char):
            text = text.replace(char, " ")

    for r in alpha_replace_saves:
        text = text.replace(alpha_replace_saves[r], r)

    while "  " in text:
        text = text.replace("  ", " ")

    text = text.replace(" $ ", "$")
    text = text.replace(" > ", ">")
    text = text.replace(" MHz", "MHz")
    text = text.replace(" GHz", "GHz")

    return text

def processRawText(t):
    t = t.replace("<", " ")
    t = t.replace(">", " ")
    t = t.replace("\\", " ")
    t = t.replace("/", " ")
    t = t.replace(",", " ")
    t = t.replace('"', " ")
    t = t.replace("=", " ")
    
    t = processTagText(t)

    t = t.split(" ")
    t = [el for el in t for key in keywords if key in el]
    t = ' '.join(t)

    return t

def parseSubNumeric(n):
    if type(n) != list:
        n = [n]
    
    new = []
    #make all the strings here "safe"
    for el in n:
        if len(el) == 0:
            continue

        newel = ''
        
        for char in el:
            if char.isnumeric() or char == ">" or char == ".":
                newel = newel + char
        
        if len(newel) == 0:
            continue

        while not newel[-1].isnumeric():
            newel = newel[:-1]
            if len(newel) == 0:
                break

        if len(newel) != 0:
            new.append(newel)
        
    for ind in range(len(new)):
        if new[ind][-1] == '.':
            new[ind] = new[ind][:-1]

    final = []
    for ind in range(len(new)):
        try:
            final.append(float(new[ind]))
        except ValueError as e:
            print(new[ind])
            pass
    return final

def fetchReqData(name, req):
    session = HTMLSession()
    req = session.get(req)
    tags = []
    html = req.html
    htmltext = str(req.text)
    for keytag in keytags:
        finds = [tag.text for tag in html.find(keytag)]
        tags = tags + finds 

    results = []

    for text in tags:
        for keyword in keywords:
            if keyword in text or keyword.upper() in text or keyword.lower() in text:
                results.append(processTagText(text))
                continue
    
    for keyword in keywords:
        results = results + [processRawText(htmltext[m.start() - 40 : m.start() + 40]) for m in re.finditer(keyword, htmltext)]
    
    numeric_results = []

    for result in results:
        cur = result.split(" ")
        for subresult in cur:
            numeric = subresult.replace("MHz", "").replace("GHz", "")

            if numeric.replace(" ", "") == "":
                continue
            
            #I'm adding a "." to the end of each element here
            #so that in the case there isn't a decimal point,
            #there's no error thrown and we can still get the
            #value we need
            try:
                if "$" in numeric:
                    numeric = numeric.split("$")
                    numeric = parseSubNumeric(numeric)
                    numeric = [numeric[0] - numeric[1], numeric[0] + numeric[1]]
                elif ">" in numeric:
                    numeric = numeric.split(">")
                    numeric = parseSubNumeric(numeric)
                else:
                    numeric = parseSubNumeric(numeric)
            except Exception as e:
                continue
            mult = 1

            if len(numeric) == 0:
                continue
            
            if "GHz" in subresult:
                mult = 1000
            if "GHz" not in subresult and "MHz" not in subresult:
                #what on earth is going >50 GHz? we can just assume gigahertz if the number is <50
                if sum(numeric) / len(numeric) < 50:
                    mult = 1000

            numeric = [float(el) * mult for el in numeric]
            
            if len(numeric) == 1:
                if numeric[0] < 50:
                    continue

            if len(numeric) > 1:
                #if numeric[1] - numeric[0] > 1500:
                #    continue
                if numeric[1] < numeric[0]:
                    continue
                for el in numeric:
                    if el < 50:
                        numeric.remove(el)

            numeric_results = numeric_results + [numeric]

    return numeric_results

def getSatFreq(name):
    req = SEARCH_PREFIX + name + "+downlink+frequency"
    results = fetchReqData(name, req)
    
    if len(results) == 0:
        req = SEARCH_PREFIX + name + "+satellite+downlink+frequency"
        results = fetchReqData(name, req)
    
    if len(results) == 0:
        req = SEARCH_PREFIX + name + "+satellite+downlink+frequency+MHz"
        results = fetchReqData(name, req)
    
    r = results[:3]
    s = []
    for el in r:
        if len(el) == 1:
            s.append(str( el[0] ))
        else:
            s.append(",".join([str(e) for e in el]))

    s = [el for el in s if el != ""]

    s = '|'.join(s)
    
    return s

if __name__ == "__main__":
    tle = sys.argv[1]
    with open("TLEdata/" + tle, "r") as f:
        data = [el for el in f.read().split("\n") if el != ""]
        data = [el for el in data if el[0] == '0']

    data = [el.replace("0 ", "") for el in data]
    data = [el.split(" ")[0] for el in data]

    satnames = []
    for satname in data:
        if satname not in satnames:
            satnames.append(satname)

    db = sqlite3.connect("satdata.db")
    cur = db.cursor()
    for satname in satnames:
        print("-"*50)
        print(satname)
        if len([el for el in cur.execute('select * from satdata where name="' + satname + '"')]) > 0:
            print("Skipping", satname, "...")
            continue
        freqs = getSatFreq(satname)
        print(freqs)
        cur.execute('insert into satdata (name, freqs) values ("' + satname + '", "' + freqs + '")')
        db.commit()
        time.sleep(1)
    db.close()
