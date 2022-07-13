const express = require('express')
const bodyParser = require('body-parser')
var fs = require('fs');
const {URLSearchParams} = require('url')
const sqlite3 = require('sqlite3')
const request = require('request')

const child_process = require('child_process');

const app = express()
const PORT = 9000
const IP = "0.0.0.0"

const http = require('http')
const server = http.createServer(app)

const io = require('socket.io')(server)

const serveIndex = require('serve-index');

var OBSDBNAME = "obsdata.db"
var RFIDBNAME = "rfisources.db"
var DIR = '/home/obsuser/gsingh/rfi_survey/'
var OBSDIR = DIR + "obs/"

app.use("/public", express.static(DIR + 'public'));
app.use("/obs", express.static(DIR + 'obs'));
app.use("/obs", serveIndex(DIR + 'obs'));

process.env.TZ = "America/Los_Angeles"

var obsdb = new sqlite3.Database(OBSDBNAME)
var rfidb = new sqlite3.Database(RFIDBNAME)

var modobs = "replace(replace(obs,':',''),'-','')"

var ADMIN_DATA = fs.readFileSync("./adminkeys.txt", {encoding: 'utf-8', flag: 'r'}).split("\n").filter(el => el != "")
var ADMIN_KEYS = []
var ADMIN_NAMES = []
for (var el of ADMIN_DATA){
    var spl = el.split(",")
    ADMIN_KEYS.push(spl[0])
    ADMIN_NAMES.push(spl[1])
}

var LATEST_ID_FNAME = "./latest_obs_id.txt"
var OBS_RUNNING_FNAME = "./obs_running.txt"
var QUEUE_FNAME = "./obs_queue.txt"

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
    "<=",
    ">=",
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
    return false;
}

function checkLegalVal(v){
    for (var ival of ILLEGAL_VAL_CHARS){
        if (v.includes(ival)){
            return false;
        }
    }
    return true;
}

function writeObsId(i, f, n){
    fs.writeFileSync(LATEST_ID_FNAME, i + "," + f + "," + n)
}

function writeQueue(data){
    fs.writeFileSync(QUEUE_FNAME, data.join("\n"))
}

function fetchLatestObsId(){
    return fs.readFileSync(LATEST_ID_FNAME, {encoding: 'utf-8', flag: 'r'}).split(",")[0]
}

function writeObsEnded(){
    fs.writeFileSync(OBS_RUNNING_FNAME, "0")
}

function writeObsStarted(id, freq, name){
    fs.writeFileSync(OBS_RUNNING_FNAME, "1")
    writeObsId(id, freq, name)
}

function readQueue(){
    return fs.readFileSync(QUEUE_FNAME, {encoding: 'utf-8', flag: 'r'})
}

function addToQueue(id, cfreq, name){
    var newline = id + "," + cfreq + "," + name + "\n"
    if (name == "SYSTEM_OBS"){
        fs.writeFileSync(QUEUE_FNAME, newline + readQueue())
    }
    else{
        fs.appendFileSync(QUEUE_FNAME, newline)
    }
}

function isObsRunning(){
    var isObsRunning = fs.readFileSync(OBS_RUNNING_FNAME, {encoding: 'utf-8', flag: 'r'}).replace("\n", "")
    if (isObsRunning == "1"){
        return true;
    }
    return false;
}

function fetchCurrentObsData(){
    return fs.readFileSync(LATEST_ID_FNAME, {encoding: 'utf-8', flag: 'r'})
}

function checkAndStartObs(){
    if (isObsRunning()){
        return
    }
    var queuedata = readQueue()//fs.readFileSync(QUEUE_FNAME, {encoding: 'utf-8', flag: 'r'})
    var queuedata = queuedata.split("\n").filter(el => el != "")

    if (queuedata.length == 0){
        return
    }

    var obsdata = queuedata[0]
    thisobsid = obsdata.split(",")[0]
    thisobsfreq = obsdata.split(",")[1]
    thisobsname = obsdata.split(",")[2]
    queuedata.splice(0, 1)

    writeQueue(queuedata)
    writeObsStarted(thisobsid, thisobsfreq, thisobsname)

    console.log("starting obs " + thisobsid)
    proc = child_process.spawn("python", ["startobs.py", String(thisobsid), thisobsfreq], {detached: true}, (error, stdout, stderr) => {
        if (error) {
            console.error(`error: ${error.message}`);
            return;
        }

        if (stderr) {
            console.error(`stderr: ${stderr}`);
            return;
        }

        console.log(`stdout:\n${stdout}`);
    })

    console.log(proc.pid)
}

app.get("/obslist/:flo/:fhi/:dstart/:dend", (req, res) => {
    var flo = req.params.flo
    var fhi = req.params.fhi
    var dstart = req.params.dstart
    var dend = req.params.dend

    

    while (isNaN(dstart) && dstart != "none"){
        dstart = dstart.replace(":", "").replace("-", "")
    }
    while (isNaN(dend) && dend != "none"){
        dend = dend.replace(":", "").replace("-", "")
    }

    var query_command = "SELECT DISTINCT obs, cfreq, flagged, name FROM obsdata "
    var query_items = []

    if (flo != "none"){
        query_items.push("cfreq >= " + flo)
    }
    if (fhi != "none"){
        query_items.push("cfreq <= " + fhi)
    }
    if (dstart != "none"){
        query_items.push(modobs + " >= '" + dstart + "'")
    }
    if (dend != "none"){
        query_items.push(modobs + " <= '" + dend + "'")
    }

    if (query_items.length > 0){
        query_command = query_command + "WHERE "
    }

    query_command = query_command + query_items.join(" and ")

    query_command = query_command + " order by replace(replace(obs,':',''),'-','') DESC "

    query_command = query_command + " limit 100"

    var run = obsdb.all(query_command, (err, rows) => {
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

app.get("/", (req, res) => {
    res.sendFile("public/templates/landing.html", {root: __dirname})
})

app.get("/portal", (req, res) => {
    res.sendFile("public/templates/portal.html", {root: __dirname})
})

app.get("/catalog", (req, res) => {
    res.sendFile("public/templates/catalog.html", {root: __dirname})
})

app.get("/scheduler", (req, res) => {
    res.sendFile("public/templates/scheduler.html", {root: __dirname})
})

app.get("/scanobs/:obs", (req, res) => {
    res.sendFile("public/templates/scanobs.html", {root: __dirname})
})

app.get("/scanobs/:obs/files", (req, res) => {
    request("http://" + IP + ":" + String(PORT) + "/obs/" + req.params.obs).pipe(res)
})

app.get("/scanobs/:obs/:option", (req, res) => {
    res.sendFile("public/templates/" + req.params.option + ".html", {root: __dirname})
})

app.get("/getflag/:obs", (req, res) => {
    var command = "select flagged, name from obsdata where obs='" + req.params.obs + "'"
    var run = obsdb.all(command, (err, rows) =>{
        if (err){
            console.log(err)
            res.send("Query fail")
        }
        else{
            var resp = ''
            for (var row of rows){
                for (var key of Object.keys(row)){
                    resp = resp + row[key] + ","
                }
            }
            res.send(resp)
        }
    })
})

app.get("/setobsflag/:obs/:flag/:name", (req, res) => {
    /*if (req.params.key != ADMINKEY){
        res.send("Incorrect key")
        return
    }*/

    var name = req.params.name
    var flag = req.params.flag
    while (name.includes(" ")){
        name = name.replace(" ")
    }

    if (name == "" && flag == "1"){
        res.send("Invalid name")
        return
    }

    if (!/^[a-zA-Z]+$/.test(name) && flag == "1" ){
        res.send("Invalid name")
        return
    }

    if (name == "none" && flag == "1"){
        res.send("Invalid name")
        return
    }

    query_command = "UPDATE obsdata set flagged=" + flag + ", name='" + req.params.name + "' where obs='" + req.params.obs + "'"

    var run = obsdb.run(query_command, (err, rows) => {
        if (err){
            console.log(err)
            res.send("Query fail")
        }
        else{
            res.send("OK")
        }
    })

})

app.get("/query/:query", (req, res) => {
    var query = req.params.query

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

    var sortparams = query[1].split(",")
    var limitnum = query[2]

    var legal = true;

    for (var param of searchparams){
        if (param.length != 3){
            legal = false;
        }
        var key = param[0]
        var op = param[1]
        var val = param[2]
        if (!checkLegalKey(key) || !checkLegalOp(op) || !checkLegalVal(val)){
            legal = false;
        }
    }

    //we should be sorting by a legal key
    if (!checkLegalKey(sortparams[0])){
        legal = false;
    }

    //sort setting can either be ASC or DESC
    if (sortparams[1] != "ASC" && sortparams[1] != "DESC"){
        legal = false;
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

    var run = rfidb.all(query_command, (err, rows) => {
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

app.get("/addobs/:key/:cfreq", (req, res) => {
    var key = req.params.key
    if (ADMIN_KEYS.includes(key)){
    }
    else{
        res.send("FAIL")
        return
    }

    var cfreq = req.params.cfreq

    if (isNaN(cfreq)){
        res.send("fail")
        return
    }
    
    var thisobsid = Date.now()

    var name = ADMIN_NAMES[ADMIN_KEYS.indexOf(key)]

    addToQueue(thisobsid, cfreq, name)

    checkAndStartObs()
    res.send("OK")
})

app.get("/endobs/:id", (req, res) => {
    var latest_id = fetchLatestObsId()
    var id = req.params.id
    console.log("receieved req to end obs", id)
    if (id == latest_id){
        console.log("obs " + id + " finished")
        writeObsEnded()
        checkAndStartObs()
        res.send("OK")
    }
    else{
        res.send("FAIL")
    }
})

app.get("/obsqueue", (req, res) => {
    var queuedata = fs.readFileSync(QUEUE_FNAME, {encoding: 'utf-8', flag: 'r'}).split("\n").filter(el => el != "")
    var respdata = ''
    if (isObsRunning()){
        var data = fetchCurrentObsData().split(",")
        respdata = respdata + data[1] + "," + data[2] + "\n"
    }
    for (var el of queuedata){
        var spl = el.split(",")
        var freq = spl[1]
        var name = spl[2]
        respdata = respdata + freq + "," + name + "\n"
    }
    res.send(respdata)
})

server.listen(PORT, IP)


