// # Homepage Controllers
define(['angular',
'../services/session_services'], function() {

    var homepageControllers = angular.module('homepageControllers', ['sessionServices']);

    // ## Home page controller
    homepageControllers.controller('homepageController',
        ['$scope', '$location', 'Session', function($scope, $location, Session) {

        $scope.session_info = {};
        
        $scope.go = function(path) {
            $location.path(path);
        };
        
        $scope.getLocationPath = function() {
            return $location.path();
        };
        
        $scope.setSessionInfo  = function() {
            var current_user = $location.search().user || '';
            var current_project_id = $location.search().project_id || '';
            var currents_plan_id = $location.search().plan_id || '';
            
            Session.setCurrentSessionInfo(current_user, current_project_id, currents_plan_id);
            $scope.session_info = Session.getCurrentSessionInfo();
        };
        
        $scope.setSessionInfo();
    }]);

});


