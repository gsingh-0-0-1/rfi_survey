const express = require('express')
const bodyParser = require('body-parser')
var fs = require('fs');
const {URLSearchParams} = require('url')

const app = express()
const port = 9001

const http = require('http')
const server = http.createServer(app)

const io = require('socket.io')(server)

const serveIndex = require('serve-index');

var DIR = '/home/obsuser/gsingh/rfi_survey/'
var OBSDIR = DIR + "obs/"

app.use("/public", express.static(DIR + 'public'));
app.use("/obs", express.static(DIR + 'obs'));
app.use("/obs", serveIndex(DIR + 'obs'));

process.env.TZ = "America/Los_Angeles"

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

server.listen(port, '0.0.0.0')


