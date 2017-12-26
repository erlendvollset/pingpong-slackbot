var express = require('express');
var app = express();
var path = require('path');

app.use(express.static(path.join(__dirname)));
//app.use("/fe/styles", express.static(__dirname));
//app.use("/fe/images", express.static(__dirname + '/fe/images'));
//app.use("/fe/scripts", express.static(__dirname + '/fe/scripts'));

// viewed at based directory http://localhost:8080/
app.get('/', function (req, res) {
  res.sendFile(path.join(__dirname + 'fe/index.html'));
});

//// add other routes below
//app.get('/about', function (req, res) {
//  res.sendFile(path.join(__dirname + 'fe/views/about.html'));
//});

app.listen(process.env.PORT || 8080);