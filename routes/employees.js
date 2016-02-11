 var employee= require('../models/employee');
var express = require('express');
var router = express.Router();


router.route('/employees')

   .get(function(req, res) {
  employee.find(function(err, data) {
    if (err) {
	  // insert correct status code	
      return res.send(err);
    } 
	console.log("/employees : JSON response body : " + data);
    res.json(data);
	res.end();
  });
})

//router.route('/employees')
   .post(function(req, res) {

var emp = new employee(req.body);
 emp.code = req.body.code;
 emp.name = req.body.name;
emp.city = req.body.city;

   //res.end(JSON.stringify(emp));
   
   emp.save(function(err,data) {
    if (err) {
      return res.send(err);
    }
 
   // res.send({ message: 'employee Added'});
   res.json(data);


  });
//res.end();
  
});


  
router.route('/employees/:id')
.put(function(req,res){
employee.findOne({ _id: req.params.id }, function(err,emp) {
  
emp.code = req.body.code;
 emp.name = req.body.name;
emp.city = req.body.city;
	
    
		 emp.save(function(err) {
      if (err) {
        return res.send(err);
		
                }
         
         console.log("name"+emp._id);
         console.log("name"+emp.name);
         res.json({ message: 'employee updated!' });
		   
    });
  });
  //res.end();
})
.get(function(req, res) {
  employee.findOne({ _id: req.params.id }, function(err,emp) {
      if (err) {
	  // insert correct status code	
      return res.send(err);
    } 
	console.log("/employees : JSON response body : " + emp);
    res.json(emp);
	res.end();
  });
}) 
.delete(function(req, res) {
  employee.remove({
    _id: req.params.id
  }, function(err) {
    if (err) {
      return res.send(err);
    }
 
    res.json({ message: 'Successfully deleted' });
  });
});



module.exports = router;
