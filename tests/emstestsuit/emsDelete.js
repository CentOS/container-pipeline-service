module.exports = {
  'Delete Test for EMS-APPLICATION' : function (client) {
	  client
      .url('http://localhost:3010/#/add')
      .waitForElementVisible('body', 1000)
     // .verify.title('Employee Application')
      .end();
      /*  .click('body > div.ng-scope > div > div > table > thead > tr:nth-child(2) > td:nth-child(5) > input')
	  .url('http://172.27.59.65:3000/#/getData')
	  .waitForElementVisible('body', 1000)
	  .getText('body > div.ng-scope > div > div > table > thead > tr:nth-child(2) > td:nth-child(1)',function(result){
		  this.assert.equal(result.value,'body > div.ng-scope > div > div > table > thead > tr:nth-child(2) > td:nth-child(1)');*/
		  
	  }
	//  .end();
     
  }


