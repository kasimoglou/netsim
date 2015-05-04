module.exports = function(grunt) {

    grunt.initConfig({
        // configure grunt using package.json
        pkg: grunt.file.readJSON('package.json'),

        bower: {
            target: {
                // path of require.js configuration script
                rjsConfig: 'app/scripts/config.js',
                options: {
                    exclude: ['underscore-amd', 'momentjs']
                }
            }
        },

        // configure clean operations
        clean: {
            dist: {
                src: 'dist/*'
            },
            tmp: {
                src: '.tmp'
            }
        },

        // configure copy operations
        copy: {
            multiselect: {
                files: [{
                        expand: true,
                        cwd: 'bower_components/amitava82/angular-multiselect/src/',
                        src: 'multiselect.tmpl.html',
                        dest: 'app/html/'
                }]
            },
            // copy all scripts to dist
            scripts: {
                files: [{
                    expand: true,
                    cwd: 'app/scripts/',
                    src: [
                        '**'
                    ],
                    dest: 'dist/scripts/'
                }]
            },
            css: {
                files: [{
                    cwd: '.tmp/styles',
                    src: 'main.css',
                    dest: 'dist/styles/',
                    expand: true
                }]
            },
            // copy all images to dist
            images: {
                files: [
                    // project images
                    {
                        expand: true,
                        cwd: 'app/images/',
                        src: [
                            '**'
                        ],
                        dest: 'dist/images/'
                    }
                ]
            },
            html: {
                files: [{
                    expand: true,
                    cwd: 'app/html/',
                    src: '**/*.html',
                    dest: 'dist/html/'
                }]
            }
        },

        shell: {
            multiple: {
                command: [
                    'rm -r /home/gosling/GIT/netsim/netsim_py/src/runner/nsdEditor_gui/dist/',
                    'rm -r /home/gosling/GIT/netsim/netsim_py/src/runner/nsdEditor_gui/bower_components/',
                    'mkdir /home/gosling/GIT/netsim/netsim_py/src/runner/nsdEditor_gui/bower_components/',
                    'mkdir /home/gosling/GIT/netsim/netsim_py/src/runner/nsdEditor_gui/dist/',
                    'cp -r dist/* /home/gosling/GIT/netsim/netsim_py/src/runner/nsdEditor_gui/dist',
                    'cp -r bower_components/* /home/gosling/GIT/netsim/netsim_py/src/runner/nsdEditor_gui/bower_components'
                ].join('&&')
            }
        },

        //compile compass stylesheet projects
        compass: {
            compile: {
                options: {
                    sassDir: 'app/styles',
                    cssDir: '.tmp/styles',
                    generatedImagesDir: '.tmp/images/generated',
                    imagesDir: 'app/images',
                    javascriptsDir: 'app/scripts',
                    fontsDir: 'app/styles/fonts',
                    importPath: './bower_components',
                    httpImagesPath: '/images',
                    httpGeneratedImagesPath: '/images/generated',
                    httpFontsPath: '/styles/fonts',
                    relativeAssets: false,
                    assetCacheBuster: false,
                    raw: 'Sass::Script::Number.precision = 10\n'
                }
            }
        }
    });


    /**
    * Load plug-ins
    */

    grunt.loadNpmTasks('grunt-contrib-clean');

    // copies files
    grunt.loadNpmTasks('grunt-contrib-copy');

    // compiles our compass sass stylesheets projects
    grunt.loadNpmTasks('grunt-contrib-compass');

    grunt.loadNpmTasks('grunt-shell');


    /**
    * Configure tasks
    */

    // build styles
    grunt.registerTask('styles', [
        'compass:compile'
    ]);

    // clean up build files
    grunt.registerTask('clean-build', [
        'clean:dist',
        'clean:tmp'
    ]);

    // copy files to dist directory
    grunt.registerTask('copy-dist', [
        'copy:multiselect',
        'copy:scripts',
        'copy:css',
        'copy:images',
        'copy:html'
    ]);

    // builds project and posts result to dist directory
    grunt.registerTask('build', [
        'clean-build',
        'styles',
        'copy-dist'
    ]);

    grunt.registerTask('populate', [
        'shell:multiple'
    ]);

    grunt.registerTask('default', [
        'build',
        'populate'
    ]);
};