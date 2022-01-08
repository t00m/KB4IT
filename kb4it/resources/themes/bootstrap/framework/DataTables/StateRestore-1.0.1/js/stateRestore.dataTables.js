/*! StateRestore 1.0.1
 * 2019-2020 SpryMedia Ltd - datatables.net/license
 */
(function () {
    'use strict';

    /*! Bootstrap integration for DataTables' StateRestore
     * ©2016 SpryMedia Ltd - datatables.net/license
     */
    (function (factory) {
        if (typeof define === 'function' && define.amd) {
            // AMD
            define(['jquery', 'datatables.net-dt', 'datatables.net-staterestore'], function ($) {
                return factory($);
            });
        }
        else if (typeof exports === 'object') {
            // CommonJS
            module.exports = function (root, $) {
                if (!root) {
                    root = window;
                }
                if (!$ || !$.fn.dataTable) {
                    // eslint-disable-next-line @typescript-eslint/no-var-requires
                    $ = require('datatables.net-dt')(root, $).$;
                }
                if (!$.fn.dataTable.StateRestore) {
                    // eslint-disable-next-line @typescript-eslint/no-var-requires
                    require('datatables.net-staterestore')(root, $);
                }
                return factory($);
            };
        }
        else {
            // Browser
            factory(jQuery);
        }
    }(function ($) {
        var dataTable = $.fn.dataTable;
        return dataTable.stateRestore;
    }));

})();
