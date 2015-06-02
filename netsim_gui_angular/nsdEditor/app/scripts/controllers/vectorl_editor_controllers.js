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
                    .error(function(error) {
                        console.log(error.details);
                        alert(error.details);
            });
        };

        $scope.createVectorL = function() {
            $validator.validate($scope, 'vectorl').success(function() {
                API.vectorlCreate($scope.vectorl)
                        .success(function(response) {
                            $location.path('/vectorl/' + response._id);
                })
                        .error(function(error) {
                            console.log(error.details);
                            alert(error.details);
                });
            });
        };

        $scope.fetchProjects();
    }]);

    vectorlEditorControllers.controller('vectorlController',
        ['$scope', '$routeParams', 'API', '$timeout', '$validator',
        function($scope, $routeParams, API, $timeout, $validator) {

        $scope.vectorl = {};
        $scope.output = [
            { level: '', message: 'No output messages'}
        ];
        $scope.temp = {
            load_finished: false
        };

        $scope.alerts = {
            save_success: false
        };

        $scope.readVectorl = function() {
            API.vectorlRead($routeParams.id)
                    .success(function(response) {
                        $scope.vectorl = response;
                        $scope.getProjectName($scope.vectorl.project_id);
                        $scope.temp.load_finished = true;
            })
                    .error(function(error) {
                        console.log(error.details);
                        alert(error.details);
            });
        };
        
        $scope.getProjectName = function(project_id) {
            API.projectsRead()
                    .success(function(response) {
                        var project = _.findWhere(response.results, {id: project_id});
                        $scope.temp.project_name = project.name;
            })
                    .error(function(error) {
                        console.log(error.details);
                        alert(error.details);
            });
        };

        var success_alert_timeout = null;
        $scope.saveVectorl = function(next_action) {
            API.vectorlUpdate($routeParams.id, $scope.vectorl)
                    .success(function(response) {
                        $scope.vectorl = response;
                        if (next_action === 'compile') {
                            $scope.compileVectorl();
                        } else if (next_action === 'run') {
                            $scope.runVectorl();
                        } else {
                            $scope.alerts.save_success = true;
                            success_alert_timeout = $timeout($scope.dismiss, 10000);
                        }
            })
                    .error(function(error) {
                        if (error.status === 409) {
                            $scope.vectorl._rev = error.current_object._rev;
                            $scope.saveVectorl(next_action);
                            return;
                        }
                        console.log(error.details);
                        alert(error.details);
            });
        };
        
        $scope.compileVectorl = function() {
            $scope.output = [{ level: 'INFO', message: 'Compilation started... Please Wait...'}];
            API.vectorlCompile($routeParams.id)
                .success(function(response) {
                    $scope.output = response.compiler_output;
                })
                .error(function(error) {
                    console.log(error.details);
                    alert(error.details);
                });
        };
        
        $scope.run_params = {
            steps: 1000
        };
        
        // This function is called whenever user clicks `Run` button in vectorl screen.
        // When we get the response, we show at first compiler's output and then 
        // if run failed, `stderr` output, otherwise `stdout` output. 
        $scope.runVectorl = function() {
            $validator.validate($scope, 'run_params').success(function() {
                $scope.output = [{ level: 'INFO', message: 'Running... Please Wait...'}];
                API.vectorlRun($routeParams.id, $scope.run_params)
                    .success(function(response) {
                        //console.log(response);

                        // Show compiler output at first
                        var output = [{level: '', message: 'Compiler output'}];
                        output = output.concat(response.compiler.compiler_output);

                        // If stdout message exists, show it
                        if (response.stdout !== '') {
                            output.push({level: '', message: 'Stdout output'});
                            output.push({level: 'INFO', message: response.stdout});
                        }

                        // If stderr message exists show it
                        if (response.stderr !== '') {
                            output.push({level: '', message: 'Stderr output'});
                            output.push({level: 'ERROR', message: response.stderr});
                        }

                        // print end_time and processes events
                        if (response.compiler.success) {
                            output.push({level: 'RUN_STATS', message: 'End time: ' 
                                + response.end_time + ' , Processed events: ' + response.run_steps});
                        }

                        $scope.output = output;
                    })
                    .error(function(error) {
                        console.log(error.details);
                        alert(error.details);
                    });
                })
                .error(function() {
                    $scope.output = [{ level: '', message: 'Please fix your errors and try again.'}];
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
                    .error(function(error) {
                        console.log(error.details);
                        alert(error.details);
            });
        };
        
        $scope.getProjectName = function(project_id) {
            var project = _.findWhere($scope.projects, {id: project_id});
            return project.name;
        };

        $scope.temp = {
            load_finished: false
        };
        
        
        $scope.readVectorls = function() {
            API.vectorlsRead()
                    .success(function(response) {
                        $scope.vectorls = response.results;
                        _.each($scope.vectorls, function(vectorl) {
                            vectorl.project_name = $scope.getProjectName(vectorl.project_id);
                        });
                        $scope.shown_vectorls = $scope.vectorls;
                        $scope.temp.load_finished = true;
            })
                    .error(function(error) {
                        console.log(error.details);
                        alert(error.details);
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
                    .error(function(error) {
                        console.log(error.details);
                        alert(error.details);
            });
        };

        $scope.go = function(vectorl_id) {
            $location.path('/vectorl/' + vectorl_id);
        };

        $scope.fetchProjects();
    }]);

});
