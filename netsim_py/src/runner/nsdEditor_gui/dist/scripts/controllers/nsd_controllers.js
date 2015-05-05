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

        // This method calls `projectRead` api call and fetches all
        // projects created by user.
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

        // This method calls `createNsd` api call and creates a new
        // nsd file in the database. On success, the newly created object
        // is returned and we redirect user to nsd edit screen.
        // 
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

        // ### Initializations
        
        $scope.nsd = {};
        $scope.temp = {};
        $scope.temp.environment = {};
        
        $scope.alerts = {
            save_success: false
        };

        // Loads an existing nsd from database.
        // As soon as the data is fetched, we fill
        // nsd editor's screens with the existing data (if any)
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

        // If nsd file has not any parameters specified
        // initialize object and set `simtime_scale` to its
        // default value
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
        
        // If nsd file has not contain any view,
        // add the default one (dataTable)
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
        
        // Helps us recognize selected tab, so that we can persist
        // user's state on a refresh for example.
        $scope.tabs = {
            main_selected: parseInt($location.search()['tab']) || 1
        };
        
        // Activates tab with `index` and updates `tab` query param accordingly
        $scope.setSelectedTab = function(index) {
            $scope.tabs.main_selected = index;
            $location.search('tab', index);
        };

        // ### Network tab related data and methods
        
        $scope.plans = [];
        
        // This method calls `projectPlansRead` api call and
        // fetches the plans created for project with id `project_id`
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
        
        // ### Environment related data and methods
        $scope.vectorls = [];
        
        // This method calls `projectVectorLFilesRead` api call and
        // fetches the vectorl files created for project with id `project_id`
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
        
        // ### Output tab related data and methods
        
        // Used in order to determine whether we have to show
        // plots div or not (plots div is shown when user has clicked
        // on a row in the views table)
        $scope.view = {
            selected: {},
            isSelected: false
        };
        
        $scope.setSelectedView = function(view) {
            $scope.view.selected = view;
            $scope.view.isSelected = true;
        };
        
        // This function is called when `create new view` button is clicked
        // and opens a new create_view dialog.
        $scope.createView = function() {
            var self = this;
            ngDialog.open({
                template: 'templates/create_view.html',
                className: 'ngdialog-theme-default new-view-dialog',
                closeByDocument: false,
                // This controller controls create_view template
                controller: ['$scope', function($scope) {
                        
                    // Boolean value used to customize 
                    // buttons in the template
                    // (If `$scope.mode.update` is true user has opened
                    // this view in order to update it so we have to replace
                    // create button with an update button)
                    //
                    $scope.mode = {
                        update: false
                    };
                    
                    // Base datasets are all the previously created views
                    $scope.base_datasets = self.nsd.views;
                    
                    // In `myData` all selected fields are going to be stored
                    $scope.myData = [];
                 
                    // Configuration for ng-Grid
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
                    
                    // This method is called whenever 'Add field' button is clicked
                    // in Create view screen. It adds a new editable row to fields
                    // table.
                    //
                    $scope.addField = function() {
                        $scope.myData.push({name: 'field' + $scope.myData.length, expression: '', groupby: false});
                    };
                    
                    // Called when dialog's create button is clicked and
                    // adds the newly configured view to nsd's existing views.
                    // Note that this change is not persisted at the db until
                    // user clicks `Save nsd`.
                    $scope.createView = function() {
                        
                        if ($scope.view) {
                            $scope.view.columns = [];
                            $scope.view.groupby = [];
                            
                            // transform `myData` table model to `columns` and `groupby`
                            // models accepted by nsd.
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
                    
                    // Called when dialog's cancel button is clicked - just dismisses the dialog
                    $scope.dismissDialog = function() {
                        $scope.closeThisDialog();
                    };
                }]
            });
        };
        
        // Called when user clicks `Edit` button in a row in my views table.
        // Opens `create_view` template, initializes it with selected `view`
        // data and lets user update it.
        $scope.updateView = function(view) {
            var self = this;
            ngDialog.open({
                template: 'templates/create_view.html',
                className: 'ngdialog-theme-default new-view-dialog',
                closeByDocument: false,
                controller: ['$scope', function($scope) {
                    $scope.mode = {
                        update: true
                    };
                    
                    // Initialize view with the selected one 
                    $scope.view = _.clone(view);
                    
                    $scope.base_datasets = [];
                    
                    // In `myData` all selected fields are going to be stored
                    $scope.myData = [];
                 
                    // Configuration for ng-Grid
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
                    
                    // This method is called whenever 'Add field' button is clicked
                    // in Create view screen. It adds a new editable row to fields
                    // table.
                    //
                    $scope.addField = function() {
                        $scope.myData.push({name: 'field' + $scope.myData.length, expression: '', groupby: false});
                    };
                    
                    // Form `myData` object from `columns` and `groupby`
                    // objects
                    $scope.initializeGridData = function() {
                        $scope.myData = $scope.view.columns;
                        
                        _.each($scope.myData, function(obj) {
                            if (_.contains($scope.view.groupby, obj.name)) {
                                obj.groupby = true;
                            } else {
                                obj.groupby = false;
                            }
                        });
                    };
                    
                    // When updating a view, base_datasets
                    // include all views of the selected 
                    // nsd file *except* the one that is currently
                    // edited
                    $scope.initializeBaseDatasets = function() {
                        $scope.base_datasets = _.reject(self.nsd.views, function(obj) {
                            return obj.name === $scope.view.name;
                        });
                    };
                    
                    $scope.initializeGridData();
                    $scope.initializeBaseDatasets();
                    
                    $scope.updateView = function() {
                        view.name = $scope.view.name;
                        view.table_filter = $scope.view.table_filter;
                        view.base_tables = $scope.view.base_tables;
                        
                        $scope.view.columns = [];
                        $scope.view.groupby = [];

                        // transform `myData` table model to `columns` and `groupby`
                        // models accepted by nsd.
                        _.each($scope.myData, function(obj) {
                            $scope.view.columns.push({ name: obj.name, expression: obj.expression });
                            if (obj.groupby === true) {
                                $scope.view.groupby.push(obj.name);
                            }
                        });
                        
                        view.columns = $scope.view.columns;
                        view.groupby = $scope.view.groupby;
                        
                        $scope.closeThisDialog();
                    };
                    
                    // Called when dialog's cancel button is clicked - just dismisses the dialog
                    $scope.dismissDialog = function() {
                        $scope.closeThisDialog();
                    };
                }]
            });
        };
        
        // Deletes `view` from nsd file. Note that in order that change
        // to be persisted in the database, user has to click 'Save nsd'
        $scope.deleteView = function(view) {
            var self = this;
            ngDialog.openConfirm({
                template: '<div class="ng-dialog-message">' +
                            '<p>You are about to delete <i><strong>' + view.name +'</strong></i> view.</p>' +
                            '<p>Are you sure?</p>' +
                        '</div>' +
                        '<div class="ng-dialog-buttons row">' +
                            '<a class="btn btn-sm btn-success listing-delete-dialog-btn" ng-click="deleteView()">Yes</a>' +
                            '<a class="btn btn-sm btn-default" ng-click="dismissDialog()">Cancel</a>' +
                        '</div>',
                plain: true,
                className: 'ngdialog-theme-default',
                controller: ['$scope', function($scope) {
                    $scope.deleteView = function() {
                        self.nsd.views = _.without(self.nsd.views, view);
                        $scope.closeThisDialog();
                    };
                    
                    $scope.dismissDialog = function() {
                        $scope.closeThisDialog();
                    };
                }]
            });
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
        
        // ### Save Nsd related data and functions
        
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
