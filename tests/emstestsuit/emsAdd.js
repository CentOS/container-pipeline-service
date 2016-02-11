module.exports = {
   /* 'step one' : function (browser) {
    browser
      .url('http://172.27.59.234:3010/#/home')
      .waitForElementVisible('body', 1000)
     .click('a[id=AddEmployeeLink]')
	  // .waitForElementVisible('a[id=AddEmployeeLink]', 1000)
	   
	},*/
	
  'Test for EMS-APPLICATION' : function (client) {
    client
      .url('http://localhost:3010/#/add')
      .waitForElementVisible('body', 1000)
      .assert.title('Employee Application')
      .assert.visible('input')
      .setValue('input[name=code]', '4444')
	  .setValue('input[name=name]', 'Navin')
	  .setValue('input[name=city]', 'chennai')
      .waitForElementVisible('input[id=btn_add1]', 1000)
      .click('input[id=btn_add1]')
     
  },
  'List of Employees' : function(client,browser){
	  client
	  .url('http://localhost:3010/#/add')
	  .waitForElementVisible('body', 1000)
	  .assert.title('Employee Application')
	.end();
/*	.getText('body > div.ng-scope > div > div > table > thead > tr.ng-scope > td:nth-child(1)', function(result) {
		
		console.log("value is :"+result.value);
    this.assert.equal(result.value, '4444')
*/	
	
}
	  
	  
	 // .assert.attributeEquals('body','table','Manoj1')
	 // .end();
  }

//.pause(1000)
 //     .end();
