var editController = angular.module('editController',[]);
editController.controller('EditCtrl',['$scope','$http','$location','$routeParams',function($scope,$http,$location,$routeParams){
	
	$http.get('/api/employees/' + $routeParams.id).success(function(response){
             $scope.emp=response;
    });
		 
	 $scope.update = function(){
        console.log($scope.emp._id);
         $http.put('/api/employees/' + $scope.emp._id,$scope.emp).success(function(response){
             console.log("Inside Update Function");
             console.log(response);
         });
		  $location.url('/list');
    };
    
}]);