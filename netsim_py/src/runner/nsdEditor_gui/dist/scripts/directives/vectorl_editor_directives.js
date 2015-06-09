define(['underscore',
    'codemirror/lib/codemirror',
    'codemirror/mode/clike/clike',
    'angular'], function(_, CodeMirror) {
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

    // myVectorlOutput directive
    // Displays vectorl compile and run messages to output
    vectorlEditorDirectives.directive('myVectorlOutput', [function() {
        return {
            restrict: 'EA',
            require: 'ngModel',
            scope: {
                ngModel: '='
            },
            link: function(scope, element) {
                scope.$watch('ngModel', function(output_array) {
                    scope.showOutput(output_array);
                }, true);
                
                scope.display = {
                    message: ''
                };
                
                scope.showOutput = function(output_array) {
                    scope.display.message = '';
                    _.each(output_array, function(message) {
                        var text_color_class = '';
                        if (message.level === 'INFO') {
                            text_color_class = 'text-info';
                        } else if (message.level === 'ERROR') {
                            text_color_class = 'text-danger';
                        } else if (message.level === 'WARNING') {
                            text_color_class = 'text-warning';
                        } else if (message.level === 'CRITICAL') {
                            text_color_class = 'text-danger strong';
                        } else if (message.level === 'RUN_STATS') {
                            text_color_class = 'italics strong';
                        }else {
                            text_color_class = 'text-muted italics';
                        }
                        
                        // replace newline chars with <br/>
                        var new_message = message.message.replace(/(?:\r\n|\r|\n)/g, '<br />');
                        scope.display.message += '<span class=\'' + text_color_class +'\'>' +
                                new_message + '</span><br/>';
                    });
                    element.html(scope.display.message);
                };
            }
        };
    }]);
});


