define(['angular',
    'bootstrap',
    'angular-animate',
    'angular-route',
    'angular-bootstrap',
    'angular-validator',
    'angular-validator-rules',
    'multiselect',
    './controllers/homepageControllers',
    './controllers/vectorl_editor_controllers',
    './controllers/nsd_controllers',
    './directives/vectorl_editor_directives'], function() {

    var nsdEditorApp = angular.module('nsdEditorApp', [
        'ngAnimate',
        'ngRoute',
        'ui.bootstrap',
        'ui.multiselect',
        'validator',
        'validator.rules',
        'homepageControllers',
        'vectorlEditorControllers',
        'nsdControllers',
        'vectorlEditorDirectives'
    ]);

    nsdEditorApp.config([
        '$interpolateProvider',
        function($interpolateProvider) {
            $interpolateProvider.startSymbol('[[');
            $interpolateProvider.endSymbol(']]');
        }
    ]);

    nsdEditorApp.config([
        '$locationProvider',
        function($locationProvider) {
            $locationProvider.
                html5Mode(false).
                hashPrefix('!');
        }
    ]);

    nsdEditorApp.config([
        '$routeProvider',
        function($routeProvider) {
            $routeProvider.
                when('/', {
                    templateUrl: '../html/views/nsds.html',
                    controller: 'nsdListController'
                }).
                when('/nsd/:id', {
                    templateUrl: '../html/views/nsd.html',
                    controller: 'nsdController',
                    reloadOnSearch: false
                }).
                when('/new_nsd', {
                    templateUrl: '../html/views/new_nsd_form.html',
                    controller: 'newNsdFormController'
                }).
                when('/new_vectorl', {
                    templateUrl: '../html/views/new_vectorl_form.html',
                    controller: 'newVectorlController'
                }).
                when('/vectorl/:id', {
                    templateUrl: '../html/views/vectorl.html',
                    controller: 'vectorlController'
                }).
                when('/vectorl_files', {
                    templateUrl: '../html/views/vectorls.html',
                    controller: 'vectorlListController'
                }).
                otherwise({
                    templateUrl: '../html/404.html'
                });
        }
    ]);
    
    nsdEditorApp.config(function($validatorProvider) {
        return $validatorProvider.register('notSameHilNodes', {
            invoke: 'watch',
            validator: function(value, scope) {
                if (typeof scope.nsd.hil === 'undefined') {
                    return true;
                }
                
                return value !== scope.nsd.hil.node1;
            },
            error: 'Node 2 should not match Node 1'
        });
    });


    return nsdEditorApp;

});
