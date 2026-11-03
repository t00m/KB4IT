/* Filter bar of the document tables (all documents, bookmarks, property value pages, events) and of
 * the document lists of the Quality page.
 *
 * The theme writes the bar, hidden, before the table, and the values of each row as slugs in
 * data-kb-f-<key> attributes of its Title cell. Once DataTables has set up the table, this script
 * adds a Filter button to the search box, a row of chips for the active filters below it, and
 * moves the bar below the chips.
 *
 * Several values of one property match any of them (OR); different properties must all match (AND).
 * The filtering goes through DataTables, so the row count and the search box take it into account.
 * The count on each pill is live: the rows it would show, given the search and the other filters.
 * Pills that would show nothing are hidden, and a long property shows its first values only, with a
 * "+N more" pill for the rest.
 *
 * Lists: a bar with data-kb-list="<id>" filters the elements marked data-kb-item inside the element
 * with that id, which carry the same data-kb-f-<key> attributes. A [data-kb-list-section] around a
 * list gets its .kb-dt-list-count updated and its .kb-dt-list-none shown when nothing is left.
 *
 * Other scripts add their own filters with KB4ITFilters.extend(tableId, filter), where filter has
 * test(titleCell) -> bool, chips() -> [{label, clear()}] and clear(). The events page adds the date.
 */
(function ($) {
    'use strict';
    if (!$ || !$.fn || !$.fn.dataTable) {
        return;
    }

    var tables = {};  // table id -> context of a table with a filter bar
    var LIMIT = 10;   // pills shown per property before "+N more"
    var extras = {};  // table id -> filters added by other scripts

    function titleCell(settings, index) {
        var row = settings.aoData[index] && settings.aoData[index].nTr;
        return row ? row.querySelector('td.kb-dt-title') : null;
    }

    function valuesOf(cell, key) {
        var value = cell && cell.getAttribute('data-kb-f-' + key);
        return value ? value.split(' ') : [];
    }

    // True when the cell matches every property filter, leaving out the property skip.
    function matchesGroups(cell, state, skip) {
        for (var key in state) {
            if (key === skip || !state[key].length) {
                continue;
            }
            var have = valuesOf(cell, key);
            if (!state[key].some(function (value) { return have.indexOf(value) !== -1; })) {
                return false;
            }
        }
        return true;
    }

    function matchesExtras(cell, id) {
        return (extras[id] || []).every(function (extra) { return !extra.test || extra.test(cell); });
    }

    $.fn.dataTable.ext.search.push(function (settings, data, index) {
        var ctx = tables[settings.sTableId];
        if (!ctx) {
            return true;
        }
        var cell = titleCell(settings, index);
        return matchesExtras(cell, ctx.id) && matchesGroups(cell, ctx.state, null);
    });

    // The words of the search box, as DataTables' smart search reads them: all must be in the row.
    function searchTerms(api) {
        var text = (api.search() || '').trim().toLowerCase();
        var terms = text.match(/"[^"]*"|\S+/g) || [];
        return terms.map(function (t) { return t.replace(/^"|"$/g, ''); }).filter(Boolean);
    }

    function matchesSearch(settings, index, terms) {
        if (!terms.length) {
            return true;
        }
        var row = settings.aoData[index];
        var text = (row._sFilterRow || (row._aData || []).join(' ')).toLowerCase();
        return terms.every(function (term) { return text.indexOf(term) !== -1; });
    }

    // Table rows (their Title cells) that pass the search box and the filters of other scripts.
    function tableCandidates(ctx) {
        var settings = ctx.api.settings()[0];
        var terms = searchTerms(ctx.api);
        var cells = [];
        for (var i = 0; i < settings.aoData.length; i++) {
            var cell = titleCell(settings, i);
            if (matchesSearch(settings, i, terms) && matchesExtras(cell, ctx.id)) {
                cells.push(cell);
            }
        }
        return cells;
    }

    function updateCounts(ctx) {
        var cells = ctx.candidates();
        ctx.bar.querySelectorAll('.kb-dt-facet').forEach(function (group) {
            var key = group.getAttribute('data-kb-key');
            var counts = {};
            cells.forEach(function (cell) {
                if (matchesGroups(cell, ctx.state, key)) {
                    valuesOf(cell, key).forEach(function (v) { counts[v] = (counts[v] || 0) + 1; });
                }
            });
            var pills = [];
            group.querySelectorAll('a[data-kb-value]').forEach(function (link, index) {
                var value = link.getAttribute('data-kb-value');
                var number = link.querySelector('.kb-dt-facet-n');
                if (value === '' || !number) {
                    return;
                }
                var item = link.parentNode;
                if (item.kbOrder === undefined) {
                    item.kbOrder = index;  // the order of the page: by count over the whole table
                }
                var n = counts[value] || 0;
                number.textContent = String(n);
                item.hidden = n === 0 && !item.classList.contains('uk-active');
                pills.push({item: item, n: n});
            });
            // Most rows first, as the counts are now; ties keep the order of the page.
            pills.sort(function (a, b) { return b.n - a.n || a.item.kbOrder - b.item.kbOrder; });
            var list = group.querySelector('.uk-subnav');
            var tail = list.querySelector('.kb-dt-more');
            var shown = [];
            pills.forEach(function (pill) {
                list.insertBefore(pill.item, tail);
                if (!pill.item.hidden) {
                    shown.push(pill.item);
                }
            });
            foldGroup(group, shown);
            group.hidden = shown.length === 0;
        });
    }

    // Past LIMIT pills, the rest waits behind "+N more"; chosen values always show.
    function foldGroup(group, shown) {
        var list = group.querySelector('.uk-subnav');
        var more = list.querySelector('.kb-dt-more');
        if (!more) {
            more = document.createElement('li');
            more.className = 'kb-dt-more';
            var button = document.createElement('a');
            button.href = '#';
            button.setAttribute('role', 'button');
            more.appendChild(button);
            list.appendChild(more);
            button.addEventListener('click', function (event) {
                event.preventDefault();
                event.stopPropagation();
                group.classList.toggle('kb-dt-expanded');
                foldGroup(group, group.kbShown || []);
            });
        }
        group.kbShown = shown;
        var expanded = group.classList.contains('kb-dt-expanded');
        var folded = 0;
        shown.forEach(function (item, index) {
            var fold = index >= LIMIT && !expanded && !item.classList.contains('uk-active');
            item.hidden = fold;
            folded += fold ? 1 : 0;
        });
        var extra = shown.length - LIMIT;
        more.hidden = extra <= 0;
        more.firstChild.textContent = expanded ? 'Show less' : '+' + folded + ' more';
        more.firstChild.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    }

    function pillName(link) {
        return link.firstChild ? link.firstChild.textContent.trim() : link.textContent.trim();
    }

    function clearAll(ctx) {
        Object.keys(ctx.state).forEach(function (key) { ctx.state[key] = []; });
        (extras[ctx.id] || []).forEach(function (extra) { if (extra.clear) { extra.clear(); } });
        refresh(ctx);
    }

    function renderChips(ctx) {
        var chips = [];
        (extras[ctx.id] || []).forEach(function (extra) {
            (extra.chips ? extra.chips() : []).forEach(function (chip) { chips.push(chip); });
        });
        ctx.bar.querySelectorAll('.kb-dt-facet').forEach(function (group) {
            var key = group.getAttribute('data-kb-key');
            var name = group.querySelector('.kb-dt-facet-key').textContent.trim();
            (ctx.state[key] || []).forEach(function (value) {
                var link = group.querySelector('a[data-kb-value="' + value + '"]');
                chips.push({
                    label: name + ': ' + (link ? pillName(link) : value),
                    clear: function () { ctx.state[key] = ctx.state[key].filter(function (v) { return v !== value; }); }
                });
            });
        });
        ctx.chips.textContent = '';
        ctx.chips.hidden = chips.length === 0;
        chips.forEach(function (chip) {
            var button = document.createElement('button');
            button.type = 'button';
            button.className = 'kb-dt-chip';
            button.title = 'Remove this filter';
            button.appendChild(document.createTextNode(chip.label + ' '));
            var x = document.createElement('span');
            x.setAttribute('aria-hidden', 'true');
            x.textContent = '×';
            button.appendChild(x);
            button.addEventListener('click', function () {
                chip.clear();
                refresh(ctx);
            });
            ctx.chips.appendChild(button);
        });
        if (chips.length > 1) {
            var all = document.createElement('button');
            all.type = 'button';
            all.className = 'uk-button uk-button-link kb-dt-chips-clear';
            all.textContent = 'Clear filters';
            all.addEventListener('click', function () { clearAll(ctx); });
            ctx.chips.appendChild(all);
        }
    }

    function refresh(ctx) {
        ctx.bar.querySelectorAll('.kb-dt-facet').forEach(function (group) {
            var chosen = ctx.state[group.getAttribute('data-kb-key')] || [];
            group.querySelectorAll('a[data-kb-value]').forEach(function (link) {
                var value = link.getAttribute('data-kb-value');
                var on = value === '' ? chosen.length === 0 : chosen.indexOf(value) !== -1;
                link.parentNode.classList.toggle('uk-active', on);
                link.setAttribute('aria-pressed', on ? 'true' : 'false');
            });
        });
        var n = Object.keys(ctx.state).reduce(function (sum, key) { return sum + ctx.state[key].length; }, 0);
        if (ctx.toggle) {
            ctx.toggle.querySelector('.kb-dt-facets-count').textContent = n ? String(n) : '';
            ctx.toggle.classList.toggle('kb-dt-facets-on', n > 0);
        }
        ctx.bar.querySelector('.kb-dt-facets-clear').hidden = n === 0;
        renderChips(ctx);
        ctx.apply();
    }

    function setUp(settings) {
        var id = settings.sTableId;
        var bar = document.querySelector('.kb-dt-facets[data-kb-table="' + id + '"]');
        if (!bar || tables[id]) {
            return;
        }
        var api = new $.fn.dataTable.Api(settings);
        var wrapper = api.table().container();
        var search = wrapper.querySelector('.dataTables_filter');
        var ctx = makeContext(id, bar);
        ctx.api = api;
        ctx.candidates = function () { return tableCandidates(ctx); };
        ctx.apply = function () { api.draw(); };  // draw.dt updates the counts
        var chips = ctx.chips;

        if (search) {
            search.classList.add('kb-dt-has-facets');
            if (ctx.toggle) {
                search.appendChild(ctx.toggle);
            }
            search.parentNode.insertBefore(chips, search.nextSibling);
        } else {
            wrapper.insertBefore(chips, wrapper.firstChild);
            if (ctx.toggle) {
                wrapper.insertBefore(ctx.toggle, chips);
            }
        }
        chips.parentNode.insertBefore(bar, chips.nextSibling);
        listen(ctx);

        $(settings.nTable).on('draw.dt', function () { updateCounts(ctx); });
        tables[id] = ctx;
        refresh(ctx);
    }

    // The context of a bar: its state, the Filter button (when it has properties) and the chip row.
    function makeContext(id, bar) {
        var ctx = {id: id, bar: bar, state: {}, toggle: null};
        var chips = document.createElement('div');
        chips.className = 'kb-dt-chips noprint';
        chips.hidden = true;
        ctx.chips = chips;
        if (bar.querySelector('.kb-dt-facet')) {
            var toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'uk-button uk-button-default uk-button-small kb-dt-facets-toggle noprint';
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-controls', bar.id);
            toggle.innerHTML = '<span data-uk-icon="icon: settings; ratio: 0.8"></span> Filter '
                + '<span class="kb-dt-facets-count"></span>';
            toggle.addEventListener('click', function () {
                bar.hidden = !bar.hidden;
                toggle.setAttribute('aria-expanded', bar.hidden ? 'false' : 'true');
            });
            ctx.toggle = toggle;
        }
        return ctx;
    }

    // Clicks on the pills and on the Clear filters button of the bar.
    function listen(ctx) {
        ctx.bar.addEventListener('click', function (event) {
            var link = event.target.closest('a[data-kb-value]');
            if (link) {
                event.preventDefault();
                var key = link.closest('.kb-dt-facet').getAttribute('data-kb-key');
                var value = link.getAttribute('data-kb-value');
                var chosen = ctx.state[key] || [];
                if (value === '') {
                    chosen = [];
                } else if (chosen.indexOf(value) === -1) {
                    chosen = chosen.concat([value]);
                } else {
                    chosen = chosen.filter(function (v) { return v !== value; });
                }
                ctx.state[key] = chosen;
                refresh(ctx);
            } else if (event.target.closest('.kb-dt-facets-clear')) {
                Object.keys(ctx.state).forEach(function (k) { ctx.state[k] = []; });
                refresh(ctx);
            }
        });
    }

    // A bar over plain lists (Quality page): it hides the items that do not match.
    function setUpList(bar) {
        var scope = document.getElementById(bar.getAttribute('data-kb-list'));
        if (!scope || bar.hasAttribute('data-kb-ready')) {
            return;
        }
        bar.setAttribute('data-kb-ready', '1');
        var items = Array.prototype.slice.call(scope.querySelectorAll('[data-kb-item]'));
        var ctx = makeContext(bar.getAttribute('data-kb-list'), bar);
        ctx.candidates = function () { return items; };
        ctx.apply = function () {
            items.forEach(function (item) { item.hidden = !matchesGroups(item, ctx.state, null); });
            scope.querySelectorAll('[data-kb-list-section]').forEach(function (section) {
                var all = section.querySelectorAll('[data-kb-item]').length;
                var visible = section.querySelectorAll('[data-kb-item]:not([hidden])').length;
                var count = section.querySelector('.kb-dt-list-count');
                var none = section.querySelector('.kb-dt-list-none');
                if (count) {
                    count.textContent = String(visible);
                }
                if (none) {
                    none.hidden = !(all && !visible);
                }
            });
            updateCounts(ctx);
        };
        var tools = document.createElement('div');
        tools.className = 'kb-dt-list-tools noprint';
        if (ctx.toggle) {
            tools.appendChild(ctx.toggle);
        }
        tools.appendChild(ctx.chips);
        bar.parentNode.insertBefore(tools, bar);
        listen(ctx);
        refresh(ctx);
    }

    window.KB4ITFilters = {
        extend: function (tableId, filter) {
            (extras[tableId] = extras[tableId] || []).push(filter);
            if (tables[tableId]) {
                refresh(tables[tableId]);
            }
        },
        refresh: function (tableId) {
            if (tables[tableId]) {
                refresh(tables[tableId]);
            }
        }
    };

    document.querySelectorAll('.kb-dt-facets[data-kb-list]').forEach(setUpList);

    $(document).on('init.dt', function (event, settings) {
        setUp(settings);
    });
    // A table set up before this script ran.
    $.fn.dataTable.tables().forEach(function (table) {
        setUp($(table).DataTable().settings()[0]);
    });
})(window.jQuery);
