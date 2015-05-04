// # Homepage Controllers
define(['angular'], function() {

    var homepageControllers = angular.module('homepageControllers', []);

    // ## Home page controller
    homepageControllers.controller('homepageController',
        ['$scope', '$location', function($scope, $location) {

        $scope.go = function(path) {
            $location.path(path);
        };
    }]);

});


