var mongoose=require('mongoose');
var Schema=mongoose.Schema;
 
var empSchema = new Schema({
    code : Number,
  name : String,
city: String
 
});
 
module.exports = mongoose.model('employees', empSchema);