// # Require.JS Configuration

require.config({
    baseUrl: '',
    waitSeconds: 40,
    paths: {
        underscore: '/nsdEdit/bower_components/underscore-amd/underscore',
        requirejs: '/nsdEdit/bower_components/requirejs/require.min',
        jquery: '/nsdEdit/bower_components/jquery/dist/jquery',
        'angular-route': '/nsdEdit/bower_components/angular-route/angular-route',
        'angular-mocks': '/nsdEdit/bower_components/angular-mocks/angular-mocks',
        angular: '/nsdEdit/bower_components/angular/angular',
        'angular-animate': '/nsdEdit/bower_components/angular-animate/angular-animate',
        'angular-sanitize': '/nsdEdit/bower_components/angular-sanitize/angular-sanitize',
        moment: '/nsdEdit/bower_components/momentjs/moment',
        codemirror: '/nsdEdit/bower_components/codemirror/',
        'angular-bootstrap': '/nsdEdit/bower_components/angular-bootstrap/ui-bootstrap-tpls',
        'angular-validator': '/nsdEdit/bower_components/angular-validator/dist/angular-validator',
        'angular-validator-rules': '/nsdEdit/bower_components/angular-validator/dist/angular-validator-rules',
        'ngDialog': '/nsdEdit/bower_components/ngDialog/js/ngDialog',
        'multiselect': '/nsdEdit/bower_components/amitava82/angular-multiselect/src/multiselect',
        'ngGrid': '/nsdEdit/bower_components/ng-grid/ng-grid-2.0.14.debug'
    },
    shim: {
        angular: {
            deps: [
                'jquery'
            ],
            exports: 'angular'
        },
        'angular-animate': {
            deps: [
                'angular'
            ]
        },
        'angular-route': {
            deps: [
                'angular'
            ]
        },
        'angular-mocks': {
            deps: [
                'angular'
            ]
        },
        'angular-sanitize': {
            deps: [
                'angular'
            ]
        },
        'angular-bootstrap': {
            deps: [
                'angular'
            ]
        },
        'angular-validator': {
            deps: [
                'angular'
            ]
        },
        'angular-validator-rules': {
            deps: [
                'angular'
            ]
        },
        'ngDialog': {
            deps: [
                'angular'
            ]
        },
        'multiselect': {
            deps: [
                'angular'
            ]
        },
        'ngGrid': {
            deps: [
                'jquery',
                'angular'
            ]
        }
    }
});
