var supertest = require("supertest");
var should = require("should");

// This agent refers to PORT where program is runninng.

var server = supertest.agent("http://localhost:3010");

// UNIT test begin

describe("SAMPLE unit test",function(){

  // #1 should return home page

 

    
      it("get method",function(done){

    // calling home page api
    server
    .get("/api/employees")
    .expect("Content-type",/json/)
    .expect(200) // THis is HTTP response
    .end(function(err,res){
      // HTTP status should be 200
      res.status.should.equal(200);
      // Error key should be false.
     // res.body.error.should.equal(false);
      done();
    });
  });
  
   it("post method",function(done){

    // calling home page api
    server
    .post("/api/employees")
    .expect("Content-type",/json/)
    .expect(200) // THis is HTTP response
    .end(function(err,res){
      // HTTP status should be 200
      res.status.should.equal(200);
      // Error key should be false.
     // res.body.error.should.equal(false);
      done();
    });
  });
});
