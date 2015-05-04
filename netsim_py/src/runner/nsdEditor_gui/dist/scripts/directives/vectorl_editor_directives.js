define(['codemirror/lib/codemirror',
    'codemirror/mode/clike/clike',
    'angular'], function(CodeMirror) {
    var vectorlEditorDirectives = angular.module('vectorlEditorDirectives', []);

    // myCodeEditor directive
    // Transforms a simple textarea to a code editor using `codemirror` plugin
    vectorlEditorDirectives.directive('myCodeEditor', ['$timeout', function($timeout) {
        return {
            restrict: 'EA',
            require: 'ngModel',
            scope: {
                ngModel: '='
            },
            link: function(scope, element) {
                var myCodeEditor = CodeMirror.fromTextArea(element[0], {
                    lineNumbers: true,
                    viewportMargin: Infinity,
                    mode: 'text/x-java'
                });

                // Update model whenever user types sth in the editor
                myCodeEditor.on('change', function() {
                    $timeout(function() {
                        scope.ngModel = myCodeEditor.getValue();
                    });
                });

                // Usefull only for editor initialization
                // We want `ngModel` to load and set with its value
                // editor's content
                scope.$watch('ngModel', function(value, old_value) {
                    if (value && !old_value) {
                        myCodeEditor.setValue(value);
                    }
                });
            }
        };
    }]);
});


