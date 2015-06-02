// API Services
define(['underscore', 'angular'], function(_) {

    var apiServices = angular.module('apiServices', []);

    apiServices.factory('API', ['$http', function($http) {


        function httpPromise(config) {
            var cloneConfig = _.clone(config);

            cloneConfig.url = '/api' + cloneConfig.url;

            cloneConfig.headers = {
                'Accept':'application/json',
                'Content-Type':'application/json'
            };

            return $http(cloneConfig);
        }

        // ### Specific API Calls



        // Reads projects from repository
        function apiProjectsRead() {
            var config = {
                url: '/projects',
                method: 'GET'
            };

            return httpPromise(config);
        }

        function apiProjectPlansRead(project_id) {
            var config = {
                url: '/project/' + project_id + '/plans',
                method: 'GET'
            };

            return httpPromise(config);
        }
        
        function apiPlanRead(plan_id) {
            var config = {
                url: '/plan/' + plan_id,
                method: 'GET'
            };
            
            return httpPromise(config);
        }
        
        // Creates a new nsd
        function apiNsdCreate(nsd) {
            var config = {
                url: '/nsd',
                method: 'POST',
                data: nsd
            };

            return httpPromise(config);
        }

        // Reads a specific nsd
        function apiNsdRead(id) {
            var config = {
                url: '/nsd/' + id,
                method: 'GET'
            };

            return httpPromise(config);
        }

        // Updates a specific nsd
        function apiNsdUpdate(id, nsd) {
            var config = {
                url: '/nsd/' + id,
                method: 'PUT',
                data: nsd
            };

            return httpPromise(config);
        }
        
        // Deletes a specific nsd
        function apiNsdDelete(id) {
            var config = {
                url: '/nsd/' + id,
                method: 'DELETE'
            };
            
            return httpPromise(config);
        }

        // Lists all nsds stored to the system
        function apiNsdsRead() {
            var config = {
                url: '/nsd',
                method: 'GET'
            };

            return httpPromise(config);
        }

        // Creates a new vectorl file
        function apiVectorlCreate(vectorl) {
            var config = {
                url: '/vectorl',
                method: 'POST',
                data: vectorl
            };

            return httpPromise(config);
        }

        // Fetches a specific vectorl file
        function apiVectorlRead(id) {
            var config = {
                url: '/vectorl/' + id,
                method: 'GET'
            };

            return httpPromise(config);
        }

        // Updates an existing vectorl file
        function apiVectorlUpdate(id, vectorl) {
            var config = {
                url: '/vectorl/' + id,
                method: 'PUT',
                data: vectorl
            };

            return httpPromise(config);
        }
        
        // Deletes a specific Vectorl file
        function apiVectorlDetele(id) {
            var config = {
                url: '/vectorl/' + id,
                method: 'DELETE'
            };
            
            return httpPromise(config);
        }
        
        function apiVectorlCompile(id) {
            var config = {
                url: '/vectorl/' + id + '/compile',
                method: 'GET'
            };
            
            return httpPromise(config);
        }
        
        function apiVectorlRun(id, params) {
            var url = '/vectorl/' + id + '/run';
            if (params.until) {
                url += '?until=' + params.until;
            }
            
            if (params.steps) {
                var prefix = params.until ? '&' : '?';
                url += (prefix + 'steps=' + params.steps);
            }
            
            var config = {
                url: url,
                method: 'GET'
            };
            
            return httpPromise(config);
        }

        // Lists all vectorl files stored to the system
        function apiVectorlsRead() {
            var config = {
                url: '/vectorl',
                method: 'GET'
            };

            return httpPromise(config);
        }

        // Fetches VectorL files of a specific project
        function apiProjectVectorLFilesRead(project_id) {
            var config = {
                url: '/vectorl?project_id=' + project_id ,
                method: 'GET'
            };

            return httpPromise(config);
        }


        // API Service Object
        var API = {
            // #### API Endpoint Calls

            projectsRead: apiProjectsRead,
            projectPlansRead: apiProjectPlansRead,
            planRead: apiPlanRead,
            nsdCreate: apiNsdCreate,
            nsdRead: apiNsdRead,
            nsdUpdate: apiNsdUpdate,
            nsdDelete: apiNsdDelete,
            nsdsRead: apiNsdsRead,
            vectorlCreate: apiVectorlCreate,
            vectorlRead: apiVectorlRead,
            vectorlUpdate: apiVectorlUpdate,
            vectorlDelete: apiVectorlDetele,
            vectorlCompile: apiVectorlCompile,
            vectorlRun: apiVectorlRun,
            vectorlsRead: apiVectorlsRead,
            projectVectorLFilesRead: apiProjectVectorLFilesRead
        };

        return API;
    }]);

    return apiServices;
});

