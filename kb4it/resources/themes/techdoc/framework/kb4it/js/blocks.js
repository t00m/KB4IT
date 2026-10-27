/* techdoc content blocks: copy code, fold long code, search long tables, back to top and notes for print. */
(function () {
    'use strict';

    function copyText(text, done) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
            return;
        }
        fallback(text, done);
    }

    function fallback(text, done) {
        var area = document.createElement('textarea');
        area.value = text;
        area.setAttribute('readonly', '');
        area.style.position = 'fixed';
        area.style.top = '-1000px';
        document.body.appendChild(area);
        area.select();
        try { document.execCommand('copy'); } catch (e) { /* the text is still selected */ }
        document.body.removeChild(area);
        done();
    }

    Array.prototype.forEach.call(document.querySelectorAll('.kb-code-copy'), function (button) {
        button.addEventListener('click', function () {
            var box = button.closest('.kb-code');
            var pre = box && box.querySelector('pre');
            var label = button.querySelector('.kb-code-copy-text');
            if (!pre || !label) {
                return;
            }
            copyText(pre.textContent, function () {
                if (button.kbCopyTimer) {
                    window.clearTimeout(button.kbCopyTimer);
                }
                label.textContent = 'Copied';
                button.kbCopyTimer = window.setTimeout(function () { label.textContent = 'Copy'; }, 2000);
            });
        });
    });

    Array.prototype.forEach.call(document.querySelectorAll('.kb-code-show'), function (button) {
        var box = button.closest('.kb-code');
        if (!box) {
            return;
        }
        button.setAttribute('aria-expanded', 'false');
        button.addEventListener('click', function () {
            var open = box.classList.toggle('kb-code-open');
            button.setAttribute('aria-expanded', open ? 'true' : 'false');
            button.textContent = open ? 'Show less' : 'Show all ' + button.getAttribute('data-lines') + ' lines';
        });
    });

    var totop = document.querySelector('.kb-totop');
    if (totop) {
        var toggleTotop = function () {
            totop.classList.toggle('kb-totop-visible', window.scrollY > window.innerHeight);
        };
        window.addEventListener('scroll', toggleTotop, { passive: true });
        window.addEventListener('resize', toggleTotop);
        toggleTotop();
        totop.addEventListener('click', function (event) {
            event.preventDefault();
            if (window.scrollTo) {
                try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (e) { window.scrollTo(0, 0); }
            } else {
                window.scrollTo(0, 0);
            }
        });
    }

    // Long tables of a document (marked kb-table-filter by the build) get a search box and sortable columns.
    var searched = [];
    var $ = window.jQuery;
    if ($ && $.fn && $.fn.dataTable) {
        // A column of numbers with an optional unit ("10 GB", "1,5 %") sorts by the number.
        var NUMBER = /^\s*[-+]?\d[\d.,]*\s*[^\d\s]{0,5}\s*$/;
        var order = $.fn.dataTable.ext.type.order;
        order['kb-number-pre'] = order['kb-number-pre'] || function (value) {
            var text = $('<div>').html(value).text().replace(/,(?=\d{1,2}\b)/, '.').replace(/,/g, '');
            var number = parseFloat(text);
            return isNaN(number) ? -Infinity : number;
        };
        var numberColumns = function (table) {
            var columns = [];
            $(table).find('thead tr:first > *').each(function (index) {
                var cells = $(table).find('tbody tr').map(function () {
                    return $.trim($(this).children().eq(index).text());
                }).get().filter(Boolean);
                if (cells.length && cells.every(function (text) { return NUMBER.test(text); })) {
                    columns.push(index);
                }
            });
            return columns;
        };
        $('.kb-table-filter > table').each(function () {
            // A table some other script made a DataTable is left to it.
            if ($.fn.dataTable.isDataTable(this) || this.classList.contains('kb4it-datatable')) {
                return;
            }
            searched.push($(this).DataTable({
                dom: '<"kb-table-tools"fi>t',
                paging: false,
                info: true,
                ordering: true,
                order: [],
                autoWidth: false,
                columnDefs: [{ type: 'kb-number', targets: numberColumns(this) }],
                language: { search: '', searchPlaceholder: 'Filter rows', info: '_TOTAL_ rows',
                            infoFiltered: 'of _MAX_', infoEmpty: '0 rows' }
            }));
        });
    }

    // A closed note prints as if it were open, and a searched table prints whole; the screen state comes back
    // after printing.
    var closed = [];
    var searches = [];
    window.addEventListener('beforeprint', function () {
        closed = Array.prototype.filter.call(
            document.querySelectorAll('.kb-content details'), function (note) { return !note.open; });
        closed.forEach(function (note) { note.open = true; });
        searches = searched.map(function (table) { return table.search(); });
        searched.forEach(function (table) { table.search('').draw(); });
    });
    window.addEventListener('afterprint', function () {
        closed.forEach(function (note) { note.open = false; });
        closed = [];
        searched.forEach(function (table, i) { table.search(searches[i] || '').draw(); });
        searches = [];
    });
})();
