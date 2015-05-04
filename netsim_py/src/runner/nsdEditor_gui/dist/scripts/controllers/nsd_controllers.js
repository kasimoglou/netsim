// # New nsd Controllers
define(['underscore',
    'angular',
    'ngDialog',
    'ngGrid',
    '../services/api_services'], function(_) {

    var nsdControllers = angular.module('nsdControllers', ['apiServices', 'ngDialog', 'ngGrid']);

    // New nsd form Controller
    nsdControllers.controller('newNsdFormController',
        ['$scope', '$location', '$validator', 'API', function($scope, $location, $validator, API) {

        $scope.nsd = {
            name: '',
            project_id: ''
        };
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

        $scope.createNsd = function() {
            $validator.validate($scope, 'nsd').success(function() {
                API.nsdCreate($scope.nsd)
                        .success(function(response) {
                            $location.path('/nsd/' + response._id);
                })
                        .error(function() {
                           console.log('Error creating nsd.');
                           alert('Error creating nsd.'); 
                });
            });
        };

        $scope.fetchProjects();
    }]);

    // ## nsd controller
    nsdControllers.controller('nsdController',
        ['$scope', '$routeParams', 'API', '$timeout', 'ngDialog', '$location',
        function($scope, $routeParams, API, $timeout, ngDialog, $location) {

        $scope.nsd = {};
        $scope.temp = {};
        $scope.temp.environment = {};
        
        $scope.alerts = {
            save_success: false
        };

        $scope.loadNsd = function() {
            API.nsdRead($routeParams.id)
                    .success(function(response) {
                        $scope.nsd = response;
                        $scope.initializeParameters($scope.nsd);
                        $scope.initializeEnvironment($scope.nsd);
                        $scope.initializeOutput($scope.nsd);

                        $scope.loadProjectPlans($scope.nsd.project_id);
                        $scope.loadProjectVectorlFiles($scope.nsd.project_id);
            })
                    .error(function() {
                        console.log('Error loading nsd.');
                        alert('Error loading nsd.');
            });
        };

        $scope.initializeParameters = function(nsd) {
            if (!nsd.parameters) {
                nsd.parameters = {};
                nsd.parameters.simtime_scale = -9;
            } else {
                if (!nsd.parameters.simtime_scale) {
                    nsd.parameters.simtime_scale = -9;
                }
            }
        };
        
        $scope.initializeEnvironment = function(nsd) {
            if (nsd.environment) {
                $scope.temp.env_model = nsd.environment.type;
                $scope.temp.environment.vectorl_id = nsd.environment.vectrol_id;
            }
        };
        
        $scope.initializeOutput = function(nsd) {
            if (!nsd.views) {
                nsd.views = [
                    {
                        name: 'dataTable',
                        columns: [],
                        base_tables: [],
                        table_filter: '',
                        groupby: []
                    }
                ];
            }
        };

        $scope.plans = [];

        $scope.loadProjectPlans = function(project_id) {
            API.projectPlansRead(project_id)
                    .success(function(response) {
                        $scope.plans = response.results;
            })
                    .error(function() {
                        console.log('Error fetching project\'s plans.');
                        alert('Error fetching project\'s plans.');
            });
        };

        $scope.vectorls = [];

        $scope.loadProjectVectorlFiles = function(project_id) {
            API.projectVectorLFilesRead(project_id)
                    .success(function(response) {
                        $scope.vectorls = response.results;
            })
                    .error(function() {
                        console.log('Error fetching project\'s plans.');
                        alert('Error fetching project\'s plans.');
            });
        };

        var success_alert_timeout = null;
        $scope.saveNsd = function() {
            // Save changes made to Environment tab
            if ($scope.temp.env_model === 'castalia') {
                $scope.nsd.environment = {
                    type: 'castalia'
                };
            } else if ($scope.temp.env_model === 'vectorl') {
                $scope.nsd.environment = {
                    type: 'vectorl',
                    vectrol_id: $scope.temp.environment.vectorl_id
                };
            }
            
            API.nsdUpdate($routeParams.id, $scope.nsd)
                    .success(function() {
                        $scope.alerts.save_success = true;
                        success_alert_timeout = $timeout($scope.dismiss, 10000);
            })
                    .error(function() {
                        console.log('Error updating nsd.');
                        alert('Error updating nsd.');
            });
        };

        $scope.dismiss = function() {
            $scope.alerts.save_success = false;
        };
        
        $scope.tabs = {
            main_selected: parseInt($location.search()['tab']) || 1
        };
        
        $scope.setSelectedTab = function(index) {
            $scope.tabs.main_selected = index;
            $location.search('tab', index);
        };
        
        $scope.createPlot = function() {
            var self = this;
            ngDialog.open({
                template: 'templates/create_plot.html',
                className: 'ngdialog-theme-default new-plot-dialog',
                closeByDocument: false,
                controller: ['$scope', function($scope) {
                        
                    $scope.createPlot = function() {
                        if ($scope.plot) {
                            self.nsd.plots.push($scope.plot);
                        }
                        
                        $scope.closeThisDialog();
                    };
                    
                    $scope.dismissDialog = function() {
                        $scope.closeThisDialog();
                    };
                }]
            });
        };
        
        $scope.view = {
            selected: {},
            isSelected: false
        };
        
        $scope.setSelectedView = function(view) {
            $scope.view.selected = view;
            $scope.view.isSelected = true;
        };
        
        $scope.createView = function() {
            var self = this;
            ngDialog.open({
                template: 'templates/create_view.html',
                className: 'ngdialog-theme-default new-view-dialog',
                closeByDocument: false,
                controller: ['$scope', function($scope) {
                    $scope.base_datasets = self.nsd.views;
                    
                    $scope.myData = [];
                 
                    $scope.gridOptions = { 
                        data: 'myData',
                        enableCellSelection: true,
                        enableRowSelection: false,
                        columnDefs: [
                            {
                                field: 'name', 
                                displayName: 'Name', 
                                enableCellEdit: true
                            }, 
                            {
                                field:'expression', 
                                displayName:'Expression', 
                                enableCellEdit: true
                            },
                            {
                                field:'groupby', 
                                displayName:'Group By', 
                                cellTemplate: 'templates/ng-grid_checkbox.html'
                            }
                        ]
                    };
                    
                    $scope.addField = function() {
                        $scope.myData.push({name: 'field' + $scope.myData.length, expression: '', groupby: false});
                    };
                    
                    $scope.createView = function() {
                        
                        if ($scope.view) {
                            $scope.view.columns = [];
                            $scope.view.groupby = [];

                            _.each($scope.myData, function(obj) {
                                $scope.view.columns.push({ name: obj.name, expression: obj.expression });
                                if (obj.groupby === true) {
                                    $scope.view.groupby.push(obj.name);
                                }
                            });
                        
                            self.nsd.views.push($scope.view);
                            $scope.closeThisDialog();
                        }
                        
                    };
                    
                    $scope.dismissDialog = function() {
                        $scope.closeThisDialog();
                    };
                }]
            });
        };

        $scope.$on('$destroy', function() {
            if (success_alert_timeout !== null) {
                $timeout.cancel(success_alert_timeout);
            }
        });

        $scope.loadNsd();

    }]);

    // Nsds list form Controller
    nsdControllers.controller('nsdListController',
        ['$scope', '$location', 'API', 'ngDialog', function($scope, $location, API, ngDialog) {

        $scope.nsds = [];
        $scope.projects = [];

        $scope.shown_nsds = [];

        $scope.filters = {};

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

        $scope.readNsds = function() {
            API.nsdsRead()
                    .success(function(response) {
                        $scope.nsds = response.results;
                        $scope.shown_nsds = $scope.nsds;
            })
                    .error(function() {
                        console.log('Error fetching nsds.');
                        alert('Error fetching nsds.');
            });
        };

        $scope.filterNsds = function() {
            if ($scope.filters.project_id) {
                $scope.shown_nsds = _.where($scope.nsds, {project_id: $scope.filters.project_id});
            } else {
                $scope.shown_nsds = $scope.nsds;
            }
        };
        
        $scope.confirmDeleteNsd = function(nsd_id, nsd_name) {
            var self = this;
            ngDialog.openConfirm({
                template: '<div class="ng-dialog-message">' +
                            '<p>You are about to delete <i><strong>' + nsd_name +'</strong></i> NSD file.</p>' +
                            '<p>Are you sure?</p>' +
                        '</div>' +
                        '<div class="ng-dialog-buttons row">' +
                            '<a class="btn btn-sm btn-success listing-delete-dialog-btn" ng-click="deleteNsd()">Yes</a>' +
                            '<a class="btn btn-sm btn-default" ng-click="dismissDialog()">Cancel</a>' +
                        '</div>',
                plain: true,
                className: 'ngdialog-theme-default',
                controller: ['$scope', function($scope) {
                    $scope.deleteNsd = function() {
                        $scope.closeThisDialog();
                        self.deleteNsd(nsd_id);
                    };
                    
                    $scope.dismissDialog = function() {
                        $scope.closeThisDialog();
                    };
                }]
            });
        };
        
        $scope.deleteNsd = function(nsd_id) {
            API.nsdDelete(nsd_id)
                    .success(function() {
                        $scope.readNsds();
            })
                    .error(function() {
                        console.log('Error deleting nsd.');
                        alert('Error deleting nsd.');
            });
        };

        $scope.go = function(nsd_id) {
            $location.path('/nsd/' + nsd_id);
        };

        $scope.readNsds();
        $scope.fetchProjects();
    }]);

});
