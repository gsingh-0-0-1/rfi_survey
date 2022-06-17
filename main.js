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

app.use("/public", express.static(DIR + 'public'));
app.use("/obs", express.static(DIR + 'obs'));
app.use("/obs", serveIndex(DIR + 'obs'));

process.env.TZ = "America/Los_Angeles"

app.get("/", (req, res) => {
    res.sendFile("public/templates/main.html", {root: __dirname})
})

server.listen(port, '0.0.0.0')


