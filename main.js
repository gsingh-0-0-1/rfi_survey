const express = require('express')
const bodyParser = require('body-parser')
var fs = require('fs');
const {URLSearchParams} = require('url')
const sqlite3 = require('sqlite3')
const sqlite3_sync = require("better-sqlite3");
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

var NRDZ_DIRECTORY = "/mnt/datab-netStorage-40G/visualize/plots/<sensor>/"
var NRDZ_F_LO = 410
var NRDZ_F_HI = 1790
var NRDZ_FSTEP = 20

app.use("/public", express.static(DIR + 'public'));
app.use("/obs", express.static(DIR + 'obs'));
app.use("/obs", serveIndex(DIR + 'obs'));
app.use("/followups", express.static(DIR + 'followups'));
app.use("/followups", serveIndex(DIR + 'followups'));

var obsdb = new sqlite3.Database(OBSDBNAME)
var rfidb = new sqlite3.Database(RFIDBNAME)
var rfidb_sync = new sqlite3_sync(RFIDBNAME)
var obsdb_sync = new sqlite3_sync(OBSDBNAME)

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

function writeObsId(i, n, t, p){
    fs.writeFileSync(LATEST_ID_FNAME, i + "," + n + "," + t + "," + p)
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

function writeObsStarted(id, name, type, params){
    fs.writeFileSync(OBS_RUNNING_FNAME, "1")
    writeObsId(id, name, type, params)
}

function readQueue(){
    return fs.readFileSync(QUEUE_FNAME, {encoding: 'utf-8', flag: 'r'})
}

function addToQueue(id, type, params, name){
    var newline = id + "," + name + "," + type + "," + params + "\n"

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
    thisobsname = obsdata.split(",")[1]
    thisobstype = obsdata.split(",")[2]
    thisobsparams = obsdata.split(",").slice(3)
    console.log(thisobsid, thisobsname, thisobstype, thisobsparams)
    queuedata = queuedata.slice(1)
    
    writeQueue(queuedata)

    console.log("starting obs " + thisobsid)

    writeObsStarted(thisobsid, thisobsname, thisobstype, thisobsparams)

    proc = child_process.exec("python startobs.py " + String(thisobsid) + " " + thisobstype + " " + thisobsparams, {detached: true}, (error, stdout, stderr) => {
          if (error) {
            fs.appendFileSync("errlog.txt", error.message)
            console.error(`error: ${error.message}`);
            return;
        }

        if (stderr) {
            fs.appendFileSync("errlog.txt", stderr)
            console.error(`stderr: ${stderr}`);
            return;
        }

        fs.appendFileSync("errlog.txt", stdout)
        console.log(`stdout:\n${stdout}`);
    })

    console.log(proc.pid)
}

function nrdzToUnix(dstring){
    var d = Date.parse(dstring)
    return d
}

/*
app.use((req, res, next) => {
    var url = req.url
    while (url.includes("//")){
        url = url.replace("//", "/")
    }
    if (url[url.length - 1] == '/' && url != "/"){
        url = url.slice(0, -1)
        console.log(url)
        res.redirect(301, url)
    }
    else{
        next()
    }
})
*/

app.use((req, res, next) => {
    if (req.path.substr(-1) === '/' && req.path.length > 1) {
        const query = req.url.slice(req.path.length)
        const safepath = req.path.slice(0, -1).replace(/\/+/g, '/')
        res.redirect(301, safepath + query)
    }
    else{
        next()
    }
})

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

    query_command = query_command + " limit 300"

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

app.get("/specoccdata/:freq/:bw/:dlo/:dhi", (req, res) => {
    var freq = req.params.freq
    var bw = req.params.bw
    var dlo = req.params.dlo
    var dhi = req.params.dhi

    if ((isNaN(dlo) || dlo == '') && dlo != "none"){
        res.send("Invalid request")
        return
    }

    if ((isNaN(dhi) || dhi == '') && dhi != "none"){
        res.send("Invalid request")
        return
    }

    if (isNaN(freq) || isNaN(bw)){
        res.send("Invalid request")
        return
    }

    freq = freq * 1
    bw = bw * 1

    var flo = freq - (bw / 2)
    var fhi = freq + (bw / 2)

    query_command = "select start_az, end_az, elev from rfisources where cfreq >= " + flo + " and cfreq <= " + fhi
    
    if (dhi != "none"){
        query_command = query_command + " and replace(replace(obs,':',''),'-','') <= '" + dhi + "'"
    }
    if (dlo != "none"){
        query_command = query_command + " and replace(replace(obs,':',''),'-','') >= '" + dlo + "'"
    }
    
    console.log(query_command)
    var run = rfidb.all(query_command, (err, rows) => {
        if (err){
            console.log(err)
        }
        if (rows == undefined){
            res.send("error")
            return
        }
        var resp_1 = ''
        for (var row of rows){
            resp_1 = resp_1 + (Math.round(100 * (row["start_az"] + row["end_az"]) / 2) / 100) + "," + row["elev"] + "\n"
        }
        
        var obsflo = flo - 336
        var obsfhi = fhi + 336

        var run2 = obsdb.all("select distinct obs from obsdata where cfreq >= " + obsflo + " and cfreq <= " + obsfhi, (err, rows) => {
            if (err){
                console.log(err)
            }
            var n_obs = rows.length
            res.send(n_obs + "|" + resp_1)
        })

    })


    /*var data = rfidb_sync.prepare(query_command).all()
    var resp = ''
    for (var row of data){
        resp = resp + Math.round((row["start_az"] + row["end_az"]) / 2) + "," + row["elev"] + "\n"
    }

    var obsflo = freq - 336
    var obsfhi = freq + 336

    var totalobs = obsdb_sync.prepare("select distinct obs from obsdata where cfreq >= " + obsflo + " and cfreq <= " + obsfhi).all()
    var n_obs = totalobs.length
    res.send(n_obs + "|" + resp)*/
})

app.get("/dev/:item", (req, res) => {
    res.sendFile("public/dev/" + req.params.item + ".html", {root: __dirname})
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

app.get("/specocc/:freq?/:bw?", (req, res) => {
    res.sendFile("public/templates/specocc.html", {root: __dirname})
})

app.get("/scanobs/:obs", (req, res) => {
    res.sendFile("public/templates/scanobs.html", {root: __dirname})
})

app.get("/scanobs/:obs/files", (req, res) => {
    request("http://" + IP + ":" + String(PORT) + "/obs/" + req.params.obs).pipe(res)
})

app.get("/scanobs/:obs/:option/", (req, res) => {
    res.sendFile("public/templates/" + req.params.option + ".html", {root: __dirname})
})

app.get("/nrdzscanlist/:dlo/:dhi", (req, res) => {
    var l = fs.readdirSync(NRDZ_DIRECTORY.replace("<sensor>", "HCRO-NRDZ-CHIME") + NRDZ_F_LO + "/spectrograms/")
    
    var dlo = req.params.dlo
    var dhi = req.params.dhi
   
    for (let i = 0; i < l.length; i++){
        l[i] = l[i].split("D")[1].split("M")[0]
        l[i] = l[i].slice(0,4) + "-" + l[i].slice(4)
        l[i] = l[i].slice(0,7) + "-" + l[i].slice(7)
        l[i] = l[i].slice(0,13) + ":" + l[i].slice(13)
        l[i] = l[i].slice(0,16) + ":" + l[i].slice(16)
    }
   
    if (dlo != "none"){
        dlo = nrdzToUnix(dlo)
        l = l.filter(el => nrdzToUnix(el) >= dlo)
    }

    if (dhi != "none"){
        dhi = nrdzToUnix(dhi)
        l = l.filter(el => nrdzToUnix(el) <= dhi)
    }

    for (let i = 0; i < l.length; i++){
        l[i] = l[i].replace("T", "")
        l[i] = l[i].slice(0,10) + "-" + l[i].slice(10)
    }
    
    res.send(l.join("\n"))
})

app.get("/nrdzscans", (req, res) => {
    res.sendFile("public/templates/nrdz/portal.html", {root: __dirname})
})

app.get("/nrdzscan/:obs", (req, res) => {
    res.sendFile("public/templates/nrdz/nrdzscan.html", {root: __dirname})
})

app.get("/nrdzscan/:obs/:option/:sensor", (req, res) => {
    res.sendFile("public/templates/nrdz/option.html", {root: __dirname}) 
})

app.get("/nrdzimages/:option/:sensor/:freq/:time", (req, res) => {
    var path = NRDZ_DIRECTORY.replace("<sensor>", req.params.sensor) + req.params.freq + "/" + req.params.option + "/"
    var img = fs.readdirSync(path).filter(el => el.includes(req.params.time))[0]
    if (img == undefined){
        res.send("No image found")
    }
    else{
        res.sendFile(path + img)
    }
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

function correctQueryItem(item){
    if (item == 'az'){
        item = '0.5*(start_az + end_az)'
    }
    if (item == 'eaw'){
        item = 'COS(RADIANS(elev))*(end_az-start_az)'
    }
    if (item == 'ant'){
        item = 'antlo'
    }
    if (item == 'sat'){
        item = 'source_sat'
    }
    if (item == 'el'){
        item = 'elev'
    }
    return item
}

app.get("/query/:query", (req, res) => {
    var query = req.params.query
    var query_spl = query.split("|")

    var fetch_items = query_spl[0].split(",")
    var query_items = query_spl[1].split(":")
    var order_by = query_spl[2]
    var limit = query_spl[3]

    var query_command = 'SELECT '
    
    var fetch = []

    for (var fetch_item of fetch_items){
        let item = fetch_item
        item = correctQueryItem(item)
        fetch.push(item)
    }

    query_command = query_command + fetch.join(", ") + " from rfisources "

    var conditions = []

    for (var query_item of query_items){
        var condition = '('
        let item = query_item.split(",")//.filter(el => el != "")
        if (item[1] == '' && item[2] == ''){
            continue
        }

        item[0] = correctQueryItem(item[0])

        if (item[0] == 'obs'){
            item[0] = "replace(replace(obs,':',''),'-','')"
        }

        if (item[0] == 'antlo' || item[0].includes('source')){
            var alikes = []
            for (let i = 1; i < item.length; i++){
                if (item[i] == "NOTNULL"){
                    alikes.push(item[0] + " IS NOT NULL ")
                    continue
                }
                if (item[i] == ''){
                    alikes.push(item[0] + " IS NOT NULL or " + item[0] + " IS NULL ")
                    continue
                }
                alikes.push(item[0] + " LIKE '%" + item[i] + "%'")
            }
            condition = condition + " " + alikes.join(" or ")
        }
        else{
            var comparisons = []
            if (item[1] != undefined && item[1] != ""){
                comparisons.push(item[0] + " >= " + item[1])
            }
            if (item[2] != undefined && item[2] != ""){
                comparisons.push(item[0] + " <= " + item[2])
            }
            condition = condition + " " + comparisons.join(" and ")
        }
        condition = condition + ")"
       
        if (condition != "()"){
            conditions.push(condition)
        }
    }

    conditions = conditions.join(" and ")
    if (conditions != ""){
        query_command = query_command + " WHERE " + conditions
    }

    order_by = order_by.split(",")

    if (order_by.length != 2 || !(order_by[1] == "ASC" || order_by[1] == "DESC")){
        console.log(order_by)
        return
    }

    query_command = query_command + " ORDER BY " + order_by[0] + " " + order_by[1]

    if (isNaN(limit)){
        return
    }

    query_command = query_command + " LIMIT " + limit

    console.log(query_command)
    var run = rfidb.all(query_command, (err, rows) => {
        if (err){
            console.log(err)
        }
        if (rows == undefined){
            return
        }
        res.send(JSON.stringify(rows))
    })
})

app.get("/addobs/:key/:type/:params", (req, res) => {
    var key = req.params.key
    if (ADMIN_KEYS.includes(key)){
    }
    else{
        res.send("FAIL")
        return
    }

    var type = req.params.type
    var params = req.params.params

    var thisobsid = Date.now()

    var name = ADMIN_NAMES[ADMIN_KEYS.indexOf(key)]

    addToQueue(thisobsid, type, params, name)

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
        respdata = respdata + data.slice(1).join(",") + "\n"
    }
    for (var el of queuedata){
        var spl = el.split(",")
        respdata = respdata + spl.slice(1).join(",") + "\n"
    }
    res.send(respdata)
})

server.listen(PORT, IP)


