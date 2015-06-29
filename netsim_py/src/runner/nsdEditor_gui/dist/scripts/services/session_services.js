define(['angular'], function() {
    var sessionServices = angular.module('sessionServices',[]);
    
    sessionServices.factory('Session', function() {
        var session_info = {
            current_user: '',
            current_project_id: '',
            current_plan_id: ''
        };
        
        var Session = {
            setCurrentSessionInfo: function(user, project, plan) {
                session_info.current_user = user;
                session_info.current_project_id = project;
                session_info.current_plan_id = plan;
            },
            
            getCurrentSessionInfo: function() {
                return session_info;
            }
        };
        return Session;
    });
});


