myApp.controller('AppCtrl',['$scope','$http','$location',function($scope,$http,$location){
    console.log("hello world from controller");
    
    $http.get('/api/employees').success(function(response){
        $scope.employee1 = response; 
    });