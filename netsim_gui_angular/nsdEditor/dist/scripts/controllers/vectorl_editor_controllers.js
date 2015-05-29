// # Vectorl editor Controllers
define(['angular',
    'ngDialog',
    '../services/api_services'], function() {

    var vectorlEditorControllers = angular.module('vectorlEditorControllers', ['apiServices', 'ngDialog']);

    // ## New Vectorl controller
    vectorlEditorControllers.controller('newVectorlController',
        ['$scope', '$location', '$validator', 'API', function($scope, $location, $validator, API) {

        $scope.vectorl = {};
        $scope.projects = [];

        $scope.fetchProjects = function() {
            API.projectsRead()
                    .success(function(response) {
                        $scope.projects = response.results;
            })
                    .error(function() {
                        console.log('Error during fetching projects from repository.');
                        alert('Error during fetching projects from repository.');
            });
        };

        $scope.createVectorL = function() {
            $validator.validate($scope, 'vectorl').success(function() {
                API.vectorlCreate($scope.vectorl)
                        .success(function(response) {
                            $location.path('/vectorl/' + response._id);
                })
                        .error(function() {
                            console.log('Error creating vectorl.');
                            alert('Error creating vectorl.');
                });
            });
        };

        $scope.fetchProjects();
    }]);

    vectorlEditorControllers.controller('vectorlController',
        ['$scope', '$routeParams', 'API', '$timeout',
        function($scope, $routeParams, API, $timeout) {

        $scope.vectorl = {};
        $scope.temp = {};

        $scope.alerts = {
            save_success: false
        };

        $scope.readVectorl = function() {
            API.vectorlRead($routeParams.id)
                    .success(function(response) {
                        $scope.vectorl = response;
                        $scope.getProjectName($scope.vectorl.project_id);
            })
                    .error(function() {
                        console.log('Error reading vectorl file.');
                        alert('Error reading vectorl file.');
            });
        };
        
        $scope.getProjectName = function(project_id) {
            API.projectsRead()
                    .success(function(response) {
                        var project = _.findWhere(response.results, {id: project_id});
                        $scope.temp.project_name = project.name;
            })
                    .error(function() {
                        console.log('Error reading project name');
                        alert('Error reading project name.');
            });
        };

        var success_alert_timeout = null;
        $scope.saveVectorl = function() {
            API.vectorlUpdate($routeParams.id, $scope.vectorl)
                    .success(function(response) {
                        $scope.vectorl = response;
                        $scope.alerts.save_success = true;
                        success_alert_timeout = $timeout($scope.dismiss, 10000);
            })
                    .error(function(error) {
                        if (error.status == 409) {
                            $scope.vectorl._rev = error.current_object._rev;
                            $scope.saveVectorl();
                            return;
                        }
                        console.log('Error updating vectorl file.');
                        alert('Error updating vectorl file.');
            });
        };

        $scope.dismiss = function() {
            $scope.alerts.save_success = false;
        };

        $scope.$on('$destroy', function() {
            if (success_alert_timeout !== null) {
                $timeout.cancel(success_alert_timeout);
            }
        });

        $scope.readVectorl();
    }]);

    // Vectorls list form Controller
    vectorlEditorControllers.controller('vectorlListController',
        ['$scope', '$location', 'API', 'ngDialog', function($scope, $location, API, ngDialog) {

        $scope.vectorls = [];
        $scope.projects = [];

        $scope.shown_vectorls = [];

        $scope.filters = {};

        $scope.fetchProjects = function() {
            API.projectsRead()
                    .success(function(response) {
                        $scope.projects = response.results;
                        $scope.readVectorls();
            })
                    .error(function() {
                        console.log('Error during fetching projects from repository.');
                        alert('Error during fetching projects from repository.');
            });
        };
        
        $scope.getProjectName = function(project_id) {
            var project = _.findWhere($scope.projects, {id: project_id});
            return project.name;
        };

        $scope.readVectorls = function() {
            API.vectorlsRead()
                    .success(function(response) {
                        $scope.vectorls = response.results;
                        _.each($scope.vectorls, function(vectorl) {
                            vectorl.project_name = $scope.getProjectName(vectorl.project_id);
                        });
                        $scope.shown_vectorls = $scope.vectorls;
            })
                    .error(function() {
                        console.log('Error fetching vectorl files.');
                        alert('Error fetching vectorl files.');
            });
        };

        $scope.filterVectorLs = function() {
            if ($scope.filters.project_id) {
                $scope.shown_vectorls = _.where($scope.vectorls, {project_id: $scope.filters.project_id});
            } else {
                $scope.shown_vectorls = $scope.vectorls;
            }
        };
        
        $scope.confirmDeleteVectorl = function(vectorl_id, vectorl_name) {
            var self = this;
            ngDialog.openConfirm({
                template: '<div class="ng-dialog-message">' +
                            '<p>You are about to delete <i><strong>' + vectorl_name +'</strong></i> VectorL file.</p>' +
                            '<p>Are you sure?</p>' +
                        '</div>' +
                        '<div class="ng-dialog-buttons row">' +
                            '<a class="btn btn-sm btn-success listing-delete-dialog-btn" ng-click="deleteVectorl()">Yes</a>' +
                            '<a class="btn btn-sm btn-default" ng-click="dismissDialog()">Cancel</a>' +
                        '</div>',
                plain: true,
                className: 'ngdialog-theme-default',
                controller: ['$scope', function($scope) {
                    $scope.deleteVectorl = function() {
                        $scope.closeThisDialog();
                        self.deleteVectorl(vectorl_id);
                    };
                    
                    $scope.dismissDialog = function() {
                        $scope.closeThisDialog();
                    };
                }]
            });
        };
        
        $scope.deleteVectorl = function(vectorl_id) {
            API.vectorlDelete(vectorl_id)
                    .success(function() {
                        $scope.readVectorls();
            })
                    .error(function() {
                        console.log('Error deleting vectorl file.');
                        alert('Error deleting vectorl file.');
            });
        };

        $scope.go = function(vectorl_id) {
            $location.path('/vectorl/' + vectorl_id);
        };

        $scope.fetchProjects();
    }]);

});
