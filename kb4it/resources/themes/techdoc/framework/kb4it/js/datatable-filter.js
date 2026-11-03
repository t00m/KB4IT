/* Filter bar of the document tables (all documents, bookmarks, property value pages).
 *
 * The theme writes the bar, hidden, before the table, and the values of each row as slugs in
 * data-kb-f-<key> attributes of its Title cell. Once DataTables has set up the table, this script
 * moves the bar below the search box and adds a Filter button to open it.
 *
 * Several values of one property match any of them (OR); different properties must all match (AND).
 * The filtering goes through DataTables, so the row count and the search box take it into account.
 */
(function ($) {
    'use strict';
    if (!$ || !$.fn || !$.fn.dataTable) {
        return;
    }

    var active = {};  // table id -> {property slug -> [value slugs]}

    $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
        var state = active[settings.sTableId];
        if (!state) {
            return true;
        }
        var row = settings.aoData[dataIndex].nTr;
        var cell = row && row.querySelector('td.kb-dt-title');
        for (var key in state) {
            var wanted = state[key];
            if (!wanted.length) {
                continue;
            }
            var have = ((cell && cell.getAttribute('data-kb-f-' + key)) || '').split(' ');
            var hit = wanted.some(function (value) { return have.indexOf(value) !== -1; });
            if (!hit) {
                return false;
            }
        }
        return true;
    });

    function selectedCount(state) {
        return Object.keys(state).reduce(function (n, key) { return n + state[key].length; }, 0);
    }

    function setPressed(link, on) {
        link.parentNode.classList.toggle('uk-active', on);
        link.setAttribute('aria-pressed', on ? 'true' : 'false');
    }

    function refresh(bar, state, toggle, api) {
        bar.querySelectorAll('.kb-dt-facet').forEach(function (group) {
            var chosen = state[group.getAttribute('data-kb-key')] || [];
            group.querySelectorAll('a[data-kb-value]').forEach(function (link) {
                var value = link.getAttribute('data-kb-value');
                setPressed(link, value === '' ? chosen.length === 0 : chosen.indexOf(value) !== -1);
            });
        });
        var n = selectedCount(state);
        toggle.querySelector('.kb-dt-facets-count').textContent = n ? String(n) : '';
        toggle.classList.toggle('kb-dt-facets-on', n > 0);
        bar.querySelector('.kb-dt-facets-clear').hidden = n === 0;
        api.draw();
    }

    function setUp(settings) {
        var id = settings.sTableId;
        var bar = document.querySelector('.kb-dt-facets[data-kb-table="' + id + '"]');
        if (!bar || bar.hasAttribute('data-kb-ready')) {
            return;
        }
        bar.setAttribute('data-kb-ready', '1');
        var api = new $.fn.dataTable.Api(settings);
        var state = active[id] = {};

        var toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'uk-button uk-button-default uk-button-small kb-dt-facets-toggle noprint';
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-controls', bar.id);
        toggle.innerHTML = '<span data-uk-icon="icon: settings; ratio: 0.8"></span> Filter '
            + '<span class="kb-dt-facets-count"></span>';

        var search = api.table().container().querySelector('.dataTables_filter');
        if (search) {
            search.classList.add('kb-dt-has-facets');
            search.appendChild(toggle);
            search.parentNode.insertBefore(bar, search.nextSibling);
        } else {
            var wrapper = api.table().container();
            wrapper.insertBefore(bar, wrapper.firstChild);
            wrapper.insertBefore(toggle, bar);
        }

        toggle.addEventListener('click', function () {
            bar.hidden = !bar.hidden;
            toggle.setAttribute('aria-expanded', bar.hidden ? 'false' : 'true');
        });

        bar.addEventListener('click', function (event) {
            var link = event.target.closest('a[data-kb-value]');
            if (link) {
                event.preventDefault();
                var key = link.closest('.kb-dt-facet').getAttribute('data-kb-key');
                var value = link.getAttribute('data-kb-value');
                var chosen = state[key] || [];
                if (value === '') {
                    chosen = [];
                } else if (chosen.indexOf(value) === -1) {
                    chosen = chosen.concat([value]);
                } else {
                    chosen = chosen.filter(function (v) { return v !== value; });
                }
                state[key] = chosen;
                refresh(bar, state, toggle, api);
            } else if (event.target.closest('.kb-dt-facets-clear')) {
                Object.keys(state).forEach(function (k) { state[k] = []; });
                refresh(bar, state, toggle, api);
            }
        });
    }

    $(document).on('init.dt', function (event, settings) {
        setUp(settings);
    });
    // A table set up before this script ran.
    $.fn.dataTable.tables().forEach(function (table) {
        setUp($(table).DataTable().settings()[0]);
    });
})(window.jQuery);
