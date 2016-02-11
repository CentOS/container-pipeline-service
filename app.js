var express = require('express');
var bodyParser = require('body-parser');
var mongoose = require('mongoose');
var employees = require('./routes/employees'); //routes are defined here
var app = express(); //Create the Express app

app.use(bodyParser.urlencoded({ extended: false }))
app.use(express.static(__dirname + "/html"));
// parse application/json
app.use(bodyParser.json())

//app.use(bodyParser.text({ type: 'text/html' }))

app.use(bodyParser.urlencoded( { extended : true}));
app.use('/api', employees); //This is our route middleware



var dbName = 'test';
var connectionString = 'mongodb://172.27.59.185:27017/' + dbName;
mongoose.connect(connectionString);
//module.exports = app;


app.set('port', process.env.PORT || 3010);

 
var server = app.listen(app.get('port'), function() {
  console.log('Express server listening on port ' + server.address().port);
});
