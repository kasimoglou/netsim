// # Homepage Controllers
define(['underscore',
    'angular'], function(_) {

    var homepageControllers = angular.module('homepageControllers', []);

    // ## Home page controller
    homepageControllers.controller('homepageController',
        ['$scope', '$location', 'API', function($scope, $location, API) {

        $scope.session_info = {};
        
        $scope.go = function(path) {
            $location.path(path);
        };
        
        $scope.getLocationPath = function() {
            return $location.path();
        };
        
        $scope.getSessionInfo = function() {
            API.sessionInfo()
            .success(function(response) {
                $scope.session_info = response;
            })
            .error(function(error) {
                console.log(error.details);
                alert(error.details);
            });
        };
        
        $scope.getSessionInfo();
    }]);

});


