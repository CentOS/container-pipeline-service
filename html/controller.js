var myApp = angular.module('myApp',['ngRoute','editController']);
myApp.controller('AppCtrl',['$scope','$http','$location',function($scope,$http,$location){
    console.log("hello world from controller");
    
    $http.get('/api/employees').success(function(response){
        $scope.employee1 = response; 
    });
    
      $scope.add= function(){
       $http.post('/api/employees',$scope.emp).success(function(response){
            console.log(response);
        });
        $location.url('/list');
    };
    

     $scope.remove = function(id){
		 $http.delete('/api/employees/' + id).success(function(response){
				console.log(response);
		 });
		 $http.get('/api/employees').success(function(response){
			$scope.employee1 = response; 
		});
	 };

	 $scope.edit = function(id){
         $location.url('/edit/'+id);
     };
    $scope.goToAdd = function()
    {
        $location.url('/add');
    }
    $scope.goToList = function()
    {
        $location.url('/list');
    }
    
}]);

myApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/home', {
        templateUrl: 'home.html',
        controller: 'AppCtrl'
      }).
      when('/add', {
        templateUrl: 'add.html',
        controller: 'AppCtrl'
      }).
      when('/list', {
        templateUrl: 'list.html',
        controller: 'AppCtrl'
      }). 
	  when('/edit/:id', {
        templateUrl: 'edit.html',
        controller: 'EditCtrl'
      }). 
      otherwise({
        redirectTo: '/home'
      });
  }]);