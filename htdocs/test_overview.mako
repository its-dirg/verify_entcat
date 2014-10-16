<!DOCTYPE html>

<html ng-app="main">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="static/bootstrap-3.2/css/bootstrap.min.css" rel="stylesheet" media="screen">
    <link href="style.css" rel="stylesheet" media="all">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <script src="static/jquery.min.1.9.1.js"></script>
    <script src="static/angular.min.js"></script>
    <script src="static/bootstrap-3.2/js/bootstrap.min.js"></script>

    <title>verify_entcat: Test overview</title>

    <style media="screen" type="text/css">
        /*
         * Use visibility: collapse, instead of default display: none, on table cells to preserve the width of cells
         * without data. For use with Angular.js's ng-show/ng-hide.
         */
        td.ng-hide {
            visibility: hidden;
            display: block !important;
        }

        /* Increase max width of Bootstrap popover to allow space for bullet lists */
        .popover {
            max-width: 300px;
        }

        .btn-ok,
        .btn-too-many,
        .btn-too-few,
        .btn-too-many-and-few {
            color: #333333;
            border-color: #cccccc;
            width: 100%;
        }

        .btn-default {
            width: 100%;
        }

        .btn-ok {
            background-color: #b0e399;
        }

        .btn-too-many {
            background-color: #ff9900;
        }

        .btn-too-few {
            background-color: #fdff7f;
        }

        .btn-too-many-and-few {
            background-color: #ff7f7f;
        }

        .btn-ok:hover,
        .btn-too-many:hover,
        .btn-too-few:hover,
        .btn-too-many-and-few:hover {
            color: #333333;
            background-color: #ebebeb;
            border-color: #adadad;
        }

        /* Make the buttons appear 'unclickable' */
        .btn-ok:focus,
        .btn-ok:active:focus,
        .btn-ok.active:focus,
        .btn-too-many:focus,
        .btn-too-many:active:focus,
        .btn-too-many.active:focus,
        .btn-too-few:focus,
        .btn-too-few:active:focus,
        .btn-too-few.active:focus,
        .btn-too-many-and-few:focus,
        .btn-too-many-and-few:active:focus,
        .btn-too-many-and-few.active:focus {
            outline: none;
            outline-offset: 0;
        }

        .modal-large {
            width: 50%;
        }

        p.small {
            font-size: 1.25em;
            line-height: 1.25em;
            margin: 1.25em 0;
            text-align: left;
        }

        .ellipsis_text {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    </style>
</head>

<body>
<div class="container">
    <div class="navbar navbar-default">
        <div class="navbar-header">
            <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="#">Test overview of your IdPs category compliance</a>
        </div>
    </div>
    <div class="jumbotron">
        <p class="small">This site shows the latest test result for all IdPs.</p>

        <div id="help_instructions">
            <h2>Instructions</h2>

            <p class="small">
                Each row in the table shows the latest result (if it is known) for all tests run by an IdP.<br/>
            </p>

            <p class="small">
                The headline of each column can be clicked to view more information about the tested entity category and
                which attributes should be returned. <br/>
                Each individual test result in the table can be hovered for a complete list of the missing and/or
                extra attributes from the IdP.
            </p>
        </div>
    </div>

    <table ng-controller="TableCtrl" class="table table-bordered">
        <thead>
        <tr>
            <th><strong>IdP</strong></th>
            <th ng-repeat="data in ec_info" class="col-md-1">
                <button type="button"
                        class="btn btn-default ellipsis_text"
                        ng-click="test_button_onclick(data.name, data.desc)">
                    <strong>{{data.name}}</strong>
                </button>
            </th>
        </tr>
        </thead>

        <tbody>
        <tr ng-repeat="(idp, data) in test_results">
            <td>{{idp}}</td>
            <td class="col-md-1" ng-repeat="test in data">
                <button ng-show="has_result(test)"
                        type="button"
                        class="btn {{test.html.css_class}} ellipsis_text"
                        ng-click="test_button_onclick(test.name + ' : ' + idp, test.results_as_text)">
                    {{test.html.display_text}}
                </button>
            </td>
        </tr>
        </tbody>
    </table>
</div>

<div class="modal fade" id="testDescriptionModal" tabindex="-1" role="dialog"
     aria-labelledby="testDescriptionModal"
     aria-hidden="true">
    <div class="modal-dialog modal-large">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title" id="testDescriptionModalLabel">Test result</h4>
            </div>
            <div class="modal-body" id="testDescriptionModalBody">
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>
</body>

<script type="application/javascript">
    'use strict';

    // Enable all popovers, disabled by default in Bootstrap
    $(function () {
        $("[data-toggle='popover']").popover({
            html: true,
            trigger: 'hover',
            placement: 'bottom',
            container: 'body'
        });
    });

    var app = angular.module('main', []);
    /**
     * Controller for the table containing all test results.
     */
    app.controller('TableCtrl', function ($scope) {
        // Parse backend data for the entity categories (used for the column headers in the table)
        $scope.ec_info = [];
        var ec_info = ${ec_info}; // Descriptions and names of entity categories
        var ec_seq = ${ec_seq};  // The entity categories available for test
        for (var i = 0; i < ec_seq.length; ++i) {
            var ec = ec_seq[i];
            if (ec_info[ec]) {
                $scope.ec_info.push({name: ec_info[ec].Name, desc: ec_info[ec].Description, id: ec});
            } else {
                $scope.ec_info.push({name: ec, desc: "", id: ec});
            }
        }

        // Parse test data (from the backing database), used to populate the table
        $scope.test_results = {};
        var test_results = ${test_results};
        for (var idp in test_results) {
            $scope.test_results[idp] = [];
            for (var i = 0; i < ec_seq.length; ++i) {
                var ec = ec_seq[i];
                var test_name = ec;
                if (ec_info[ec]) {
                    test_name = ec_info[ec].Name;
                }

                var html_pres = get_HTML_presentation(test_results[idp][ec]);
                $scope.test_results[idp].push({
                    name: test_name,
                    html: html_pres,
                    results_as_text: get_result_as_text(test_results[idp][ec])
                });
            }
        }


        /**
         * Callback for the buttons in the header row of the table.
         * Shows the title and description of the test in a modal (Bootstrap).
         *
         * @param test_name name of the test
         * @param test_description description of the test
         */
        $scope.test_button_onclick = function (test_name, test_description) {
            $('#testDescriptionModalLabel').text(test_name);
            $('#testDescriptionModalBody').html(test_description);
            $('#testDescriptionModal').modal('show');
        }

        /**
         * Check whether a selected test has a recorded result for a IdP.
         *
         * @param test test entry
         * @returns {boolean} returns True if the test has a recorded result, otherwise False is returned.
         */
        $scope.has_result = function (test) {
            return test.html.display_text !== '';
        }

        /**
         * Returns a summary of the result, together with the appropriate formatting information.
         *
         * @param test_result test entry
         * @returns {{display_text: string, css_class: string}}
         */
        function get_HTML_presentation(test_result) {
            if (!test_result) {
                return {display_text: '', css_class: ''};
            }

            if (test_result.more.length == 0 && test_result.less.length == 0) {
                return {display_text: 'OK', css_class: 'btn-ok'};
            } else if ((test_result.more.length > 0) && (test_result.less.length > 0)) {
                return {display_text: 'Too few & too many', css_class: 'btn-too-many-and-few'};
            } else if (test_result.more.length > 0) {
                return {display_text: 'Too many', css_class: 'btn-too-many'};
            } else {
                return {display_text: 'Too few', css_class: 'btn-too-few'};
            }
        }

        /**
         * Returns a complete list of all missing and/or extra attributes returned in the test.
         *
         * @param test_result test entry
         * @returns {string} Formatted HTML string of the verbose result.
         */
        function get_result_as_text(test_result) {
            if (!test_result) {
                return '';
            }

            if (test_result.more.length === 0 && test_result.less.length === 0) {
                return 'Perfect match.';
            }

            var text = "";
            if (test_result.more.length > 0) {
                text = 'The following parameters should NOT be returned: <ul>';
                for (var i = 0; i < test_result.more.length; i++) {
                    text += "<li>" + test_result.more[i] + "</li>";
                }
                text += "</ul>";
            }

            if (test_result.less.length > 0) {
                text += "The following parameters should be returned: <ul>";
                for (var i = 0; i < test_result.less.length; i++) {
                    text += "<li>" + test_result.less[i] + "</li>";
                }
                text += "</ul>";
            }
            return text;
        }
    });
</script>
</html>



