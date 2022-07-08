const express = require('express')
const bodyParser = require('body-parser')
var fs = require('fs');
const {URLSearchParams} = require('url')
const sqlite3 = require('sqlite3')

const app = express()
const port = 9001

const http = require('http')
const server = http.createServer(app)

const io = require('socket.io')(server)

const serveIndex = require('serve-index');

var DBNAME = "rfisources.db"
var DIR = '/home/obsuser/gsingh/rfi_survey/'
var OBSDIR = DIR + "obs/"

app.use("/public", express.static(DIR + 'public'));
app.use("/obs", express.static(DIR + 'obs'));
app.use("/obs", serveIndex(DIR + 'obs'));

process.env.TZ = "America/Los_Angeles"

var db = new sqlite3.Database(DBNAME)

var LEGAL_KEYS = [
    "obs",
    "start_az",
    "end_az",
    "elev",
    "cfreq",
    "exceed",
    "antlo",
    "source",
    "source_az",
    "source_el"
]

var LEGAL_OPS = [
    "=",
    ">",
    "<",
    "is not",
    "IS NOT"
]

var ILLEGAL_VAL_CHARS = [
    "=",
    "INSERT",
    "insert",
    "UPDATE",
    "update",
    "SELECT",
    "select",
]

function checkLegalKey(k){
    /*if (LEGAL_KEYS.includes(k)){
        return true;
    }
    console.log(k)
    return false;*/
    //I'm going to have to work on allowing queries to do
    //math with sources... for now I'll leave this unchecked.
    return true;
}

function checkLegalOp(o){
    if (LEGAL_OPS.includes(o)){
        return true;
    }
    console.log(o)
    return false;
}

function checkLegalVal(v){
    for (var ival of ILLEGAL_VAL_CHARS){
        if (v.includes(ival)){
            return false;
        }
    }
    console.log(v)
    return true;
}

app.get("/obslist", (req, res) => {
    var files = fs.readdirSync(OBSDIR)
    files.sort().reverse()
    files = files.filter(el => !el.includes("lastscan"))
    
    var freqs = [];
    for (var file of files){
        var f = 0;
        try{
            var data = fs.readFileSync(OBSDIR + file + "/obsfreqs.txt", {encoding:'utf8', flag:'r'})
            var spl = data.split(",").filter(el => el != "")
            f = (spl[0] * 1 + spl[spl.length - 1] * 1) / 2
            f = Math.round(f) + " MHz"
        }
        catch(err){
            f = "Obs in progress"
        }
        freqs.push(f)
    }
    res.send(files.join(",") + "|" + freqs.join(","))
})

app.get("/", (req, res) => {
    res.sendFile("public/templates/landing.html", {root: __dirname})
})

app.get("/main", (req, res) => {
    res.sendFile("public/templates/main.html", {root: __dirname})
})

app.get("/catalog", (req, res) => {
    res.sendFile("public/templates/catalog.html", {root: __dirname})
})


app.get("/query/:query", (req, res) => {
    var query = req.params.query

    /*for (var bword of BLACKLIST_KEYWORDS){
        if (query.includes(bword)){
            res.send("Illegal Query")
            return
        }
    }
    for (var wword of WHITELIST_KEYWORDS){
        if (!query.includes(wword)){
            res.send("Illegal Query")
            return
        }
    }*/

    //query should be formatted as such
    //key,operator,value:key,operator,value ... |sortkey,asc/desc|limitnum
    while (query.includes("<div>")){
        query = query.replace("<div>", "/")
    }

    var query = query.split("|")

    var searchparams = query[0].split(":")
    for (var i = 0; i < searchparams.length; i++){
        searchparams[i] = searchparams[i].split(",")
    }

    console.log(searchparams)

    var sortparams = query[1].split(",")
    var limitnum = query[2]

    console.log(sortparams)
    console.log(limitnum)

    var legal = true;

    for (var param of searchparams){
        if (param.length != 3){
            legal = false;
            console.log("check 1 failed", param)
        }
        var key = param[0]
        var op = param[1]
        var val = param[2]
        if (!checkLegalKey(key) || !checkLegalOp(op) || !checkLegalVal(val)){
            legal = false;
            console.log("check 2 failed", key, op, val)
        }
    }

    //we should be sorting by a legal key
    if (!checkLegalKey(sortparams[0])){
        legal = false;
        console.log("check 3 failed", sortparams[0])
    }

    //sort setting can either be ASC or DESC
    if (sortparams[1] != "ASC" && sortparams[1] != "DESC"){
        legal = false;
        console.log("check 4 failed", sortparams[1])
    }

    if (isNaN(limitnum)){
        legal = false;
    }

    if (!legal && query[0] != ""){
        res.send("Illegal query.")
        return
    }

    var query_command = "SELECT * FROM rfisources"

    //now we know that the searchparams are legal - we can refer back to it and
    //add it to the query
    for (var i = 0; i < searchparams.length; i++){
        searchparams[i] = searchparams[i].join(" ")
    }

    var searchparams = searchparams.join(" and ")
    
    while (searchparams.includes("<cm>")){
        searchparams = searchparams.replace("<cm>", ",")
    }
    
    while (searchparams.includes("<cl>")){
        searchparams = searchparams.replace("<cl>", ":")
    }


    if (searchparams != ""){
        searchparams = " WHERE " + searchparams
    }

    query_command = query_command + " " + searchparams
    query_command = query_command + " ORDER BY " + sortparams[0] + " " + sortparams[1]
    query_command = query_command + " LIMIT " + limitnum
    console.log(query_command)
    //res.send("OK")
    //return
    //account for slashes

    //console.log(query)

    var run = db.all(query_command, (err, rows) => {
        if (err){
            console.log(err)
        }
        if (rows == undefined){
            res.send("Query error")
            return
        }
        var data = ''
        for (var row of rows){
            for (var key of Object.keys(row)){
                data = data + row[key] + ", "
            }
            data = data + "\n"
        }
        res.send(data)
    })
})
server.listen(port, '0.0.0.0')


