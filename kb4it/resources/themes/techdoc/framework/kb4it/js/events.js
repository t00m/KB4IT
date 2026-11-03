/* techdoc events page: the calendar panel beside the events table.
 *
 * The panel has a year stepper (with a list of every year), a strip of bars with the events of each
 * month, and the calendar of one month. Choosing a year, a month or a day filters the table through
 * KB4ITFilters (datatable-filter.js), which shows the choice as a chip. The address keeps it:
 * events.html#2026, #2026-03, #2026-03-24 or #all.
 */
(function () {
    'use strict';
    var root = document.querySelector('[data-kb-events]');
    var source = document.getElementById('kb-events-data');
    if (!root || !source) {
        return;
    }
    var tableId = root.getAttribute('data-kb-table');
    var days = (JSON.parse(source.textContent || '{}').days) || {};
    var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                  'October', 'November', 'December'];
    var WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

    function pad(n) { return (n < 10 ? '0' : '') + n; }
    function iso(y, m, d) { return y + '-' + pad(m) + (d ? '-' + pad(d) : ''); }
    var now = new Date();
    var today = iso(now.getFullYear(), now.getMonth() + 1, now.getDate());

    // Totals per year and per month.
    var years = {};
    var total = 0;
    Object.keys(days).forEach(function (day) {
        var y = parseInt(day.slice(0, 4), 10);
        var m = parseInt(day.slice(5, 7), 10);
        var n = days[day];
        years[y] = years[y] || {total: 0, months: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]};
        years[y].total += n;
        years[y].months[m - 1] += n;
        total += n;
    });
    var yearList = Object.keys(years).map(Number).sort(function (a, b) { return b - a; });  // newest first

    // The choice that filters the table: a year (null for all years), maybe a month, maybe a day.
    var sel = {year: null, month: null, day: null};
    // The month the calendar shows.
    var view = {year: now.getFullYear(), month: now.getMonth() + 1};

    function lastMonthWithEvents(year) {
        var months = years[year] ? years[year].months : [];
        for (var m = 12; m >= 1; m--) {
            if (months[m - 1]) {
                return m;
            }
        }
        return 1;
    }

    function defaultChoice() {
        var year = years[now.getFullYear()] ? now.getFullYear() : (yearList[0] || null);
        return {year: year, month: null, day: null};
    }

    function fromHash() {
        var hash = window.location.hash.replace('#', '');
        var match = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$/.exec(hash);
        if (hash === 'all') {
            return {year: null, month: null, day: null};
        }
        if (!match) {
            return null;
        }
        var y = parseInt(match[1], 10);
        var m = match[2] ? parseInt(match[2], 10) : null;
        var d = match[3] ? parseInt(match[3], 10) : null;
        if (m !== null && (m < 1 || m > 12)) {
            return null;
        }
        return {year: y, month: m, day: d && m ? iso(y, m, d) : null};
    }

    function hashOf(choice) {
        if (!choice.year) {
            return 'all';
        }
        return choice.day || (choice.month ? iso(choice.year, choice.month) : String(choice.year));
    }

    function prefix() {
        return sel.year ? hashOf(sel) : '';
    }

    function label(choice) {
        if (choice.day) {
            var d = parseInt(choice.day.slice(8, 10), 10);
            return d + ' ' + MONTHS[choice.month - 1] + ' ' + choice.year;
        }
        if (choice.month) {
            return MONTHS[choice.month - 1] + ' ' + choice.year;
        }
        return choice.year ? String(choice.year) : 'All years';
    }

    function countOf(choice) {
        if (!choice.year) {
            return total;
        }
        if (choice.day) {
            return days[choice.day] || 0;
        }
        if (!years[choice.year]) {
            return 0;
        }
        return choice.month ? years[choice.year].months[choice.month - 1] : years[choice.year].total;
    }

    function syncView() {
        if (sel.year && sel.month) {
            view = {year: sel.year, month: sel.month};
        } else if (sel.year) {
            view = {year: sel.year, month: sel.year === now.getFullYear() ? now.getMonth() + 1 : lastMonthWithEvents(sel.year)};
        }
    }

    // Change the choice; push adds a history entry, so the back button returns to the previous one.
    function choose(choice, push) {
        sel = {year: choice.year, month: choice.month, day: choice.day};
        syncView();
        render();
        if (window.KB4ITFilters) {
            window.KB4ITFilters.refresh(tableId);
        }
        var hash = '#' + hashOf(sel);
        if (push && window.location.hash !== hash) {
            window.history.pushState(null, '', hash);
        }
    }

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        if (text !== undefined) {
            node.textContent = text;
        }
        return node;
    }

    function plural(n) { return n + (n === 1 ? ' event' : ' events'); }

    function renderYear() {
        var box = root.querySelector('.kb-ev-year');
        box.querySelector('.kb-ev-year-name').textContent = sel.year ? String(sel.year) : 'All years';
        box.querySelector('.kb-ev-year-label').toggleAttribute('data-kb-all', !sel.year);
        box.querySelector('.kb-ev-year-count').textContent = plural(sel.year ? countOf({year: sel.year}) : total);
        var index = sel.year ? yearList.indexOf(sel.year) : -1;
        box.querySelector('[data-kb-step="older"]').disabled = !sel.year || index === yearList.length - 1;
        box.querySelector('[data-kb-step="newer"]').disabled = !sel.year || index <= 0;
        var list = box.querySelector('.kb-ev-years');
        list.textContent = '';
        [null].concat(yearList).forEach(function (year) {
            var item = el('li');
            var button = el('button', 'kb-ev-years-item' + (year === sel.year ? ' kb-ev-on' : ''));
            button.type = 'button';
            button.appendChild(el('span', '', year ? String(year) : 'All years'));
            button.appendChild(el('span', 'kb-ev-n', String(year ? years[year].total : total)));
            button.addEventListener('click', function () {
                closeYears();
                choose({year: year, month: null, day: null}, true);
            });
            item.appendChild(button);
            list.appendChild(item);
        });
    }

    function bar(text, n, max, extraClass, title, onClick, on) {
        var button = el('button', 'kb-ev-bar ' + extraClass + (on ? ' kb-ev-on' : ''));
        button.type = 'button';
        button.title = title;
        button.disabled = n === 0;
        button.setAttribute('aria-pressed', on ? 'true' : 'false');
        var track = el('span', 'kb-ev-bar-track');
        var fill = el('span', 'kb-ev-bar-fill');
        fill.style.height = (max ? Math.max(n ? 8 : 0, Math.round(100 * n / max)) : 0) + '%';
        track.appendChild(fill);
        button.appendChild(el('span', 'kb-ev-bar-n', n ? String(n) : ''));
        button.appendChild(track);
        button.appendChild(el('span', 'kb-ev-bar-label', text));
        button.addEventListener('click', onClick);
        return button;
    }

    function renderStrip() {
        var strip = root.querySelector('.kb-ev-strip');
        strip.textContent = '';
        if (sel.year) {
            var months = years[sel.year] ? years[sel.year].months : [];
            var max = Math.max.apply(null, months.concat([0]));
            for (var m = 1; m <= 12; m++) {
                (function (month) {
                    var n = months[month - 1] || 0;
                    var quarter = Math.floor((month - 1) / 3) + 1;
                    strip.appendChild(bar(MONTHS[month - 1].charAt(0), n, max, 'kb-ev-q' + quarter,
                        MONTHS[month - 1] + ' ' + sel.year + ': ' + plural(n),
                        function () {
                            var same = sel.month === month && !sel.day;
                            choose({year: sel.year, month: same ? null : month, day: null}, true);
                        }, sel.month === month));
                })(m);
            }
        } else {
            var shown = yearList.slice(0, 12).reverse();  // oldest left, newest right
            var top = Math.max.apply(null, shown.map(function (y) { return years[y].total; }).concat([0]));
            shown.forEach(function (year) {
                strip.appendChild(bar("'" + String(year).slice(2), years[year].total, top, 'kb-ev-q0',
                    year + ': ' + plural(years[year].total),
                    function () { choose({year: year, month: null, day: null}, true); }, false));
            });
        }
    }

    function moveView(step) {
        var m = view.month + step;
        var y = view.year;
        if (m < 1) { m = 12; y -= 1; }
        if (m > 12) { m = 1; y += 1; }
        if (sel.month) {  // a chosen month follows the arrows
            choose({year: y, month: m, day: null}, true);
        } else {
            view = {year: y, month: m};
            renderCalendar();
        }
    }

    function renderCalendar() {
        var cal = root.querySelector('.kb-ev-cal');
        cal.textContent = '';
        var head = el('div', 'kb-ev-cal-head');
        var prev = el('button', 'kb-ev-step', '‹');
        prev.type = 'button';
        prev.setAttribute('aria-label', 'Previous month');
        prev.addEventListener('click', function () { moveView(-1); });
        var next = el('button', 'kb-ev-step', '›');
        next.type = 'button';
        next.setAttribute('aria-label', 'Next month');
        next.addEventListener('click', function () { moveView(1); });
        var monthCount = years[view.year] ? years[view.year].months[view.month - 1] : 0;
        var title = el('button', 'kb-ev-cal-title' + (sel.month === view.month && sel.year === view.year && !sel.day ? ' kb-ev-on' : ''),
            MONTHS[view.month - 1] + ' ' + view.year);
        title.type = 'button';
        title.title = monthCount ? 'Show the ' + plural(monthCount) + ' of this month' : 'No events this month';
        title.disabled = !monthCount;
        title.addEventListener('click', function () {
            choose({year: view.year, month: view.month, day: null}, true);
        });
        head.appendChild(prev);
        head.appendChild(title);
        head.appendChild(next);
        cal.appendChild(head);

        var grid = el('div', 'kb-ev-grid');
        WEEKDAYS.forEach(function (name) { grid.appendChild(el('span', 'kb-ev-wd', name)); });
        var first = new Date(view.year, view.month - 1, 1);
        var blanks = (first.getDay() + 6) % 7;  // Monday first
        for (var b = 0; b < blanks; b++) {
            grid.appendChild(el('span', 'kb-ev-day kb-ev-blank'));
        }
        var length = new Date(view.year, view.month, 0).getDate();
        for (var d = 1; d <= length; d++) {
            (function (day) {
                var key = iso(view.year, view.month, day);
                var n = days[key] || 0;
                var classes = 'kb-ev-day' + (n ? ' kb-ev-has' : '') + (key === today ? ' kb-ev-today' : '')
                    + (sel.day === key ? ' kb-ev-on' : '');
                var cell;
                if (n) {
                    cell = el('button', classes, String(day));
                    cell.type = 'button';
                    cell.title = plural(n);
                    cell.setAttribute('aria-pressed', sel.day === key ? 'true' : 'false');
                    cell.addEventListener('click', function () {
                        var month = {year: view.year, month: view.month, day: null};
                        choose(sel.day === key ? month : {year: view.year, month: view.month, day: key}, true);
                    });
                } else {
                    cell = el('span', classes, String(day));
                }
                grid.appendChild(cell);
            })(d);
        }
        cal.appendChild(grid);

        var legend = el('div', 'kb-ev-legend');
        legend.appendChild(el('span', 'kb-ev-key kb-ev-key-event', 'Events'));
        legend.appendChild(el('span', 'kb-ev-key kb-ev-key-today', 'Today'));
        var back = el('button', 'uk-button uk-button-link kb-ev-today-link', 'Go to today');
        back.type = 'button';
        back.hidden = view.year === now.getFullYear() && view.month === now.getMonth() + 1;
        back.addEventListener('click', function () {
            view = {year: now.getFullYear(), month: now.getMonth() + 1};
            renderCalendar();
        });
        legend.appendChild(back);
        cal.appendChild(legend);
    }

    // A link to the archive page of the choice: events_YYYY.html, events_YYYYMM.html or events_YYYYMMDD.html.
    function renderFoot() {
        var foot = root.querySelector('.kb-ev-foot');
        foot.textContent = '';
        if (!sel.year || !countOf(sel)) {
            return;
        }
        var link = el('a', 'kb-ev-archive', 'Page of ' + label(sel) + ' ›');
        link.href = 'events_' + hashOf(sel).replace(/-/g, '') + '.html';
        foot.appendChild(link);
    }

    function render() {
        renderYear();
        renderStrip();
        renderCalendar();
        renderFoot();
    }

    function closeYears() {
        var list = root.querySelector('.kb-ev-years');
        list.hidden = true;
        root.querySelector('.kb-ev-year-label').setAttribute('aria-expanded', 'false');
    }

    root.querySelector('.kb-ev-year-label').addEventListener('click', function () {
        var list = root.querySelector('.kb-ev-years');
        list.hidden = !list.hidden;
        this.setAttribute('aria-expanded', list.hidden ? 'false' : 'true');
    });
    document.addEventListener('click', function (event) {
        if (!event.target.closest('.kb-ev-year')) {
            closeYears();
        }
    });
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            closeYears();
        }
    });
    root.querySelectorAll('[data-kb-step]').forEach(function (button) {
        button.addEventListener('click', function () {
            var index = yearList.indexOf(sel.year) + (button.getAttribute('data-kb-step') === 'older' ? 1 : -1);
            if (yearList[index]) {
                choose({year: yearList[index], month: null, day: null}, true);
            }
        });
    });
    window.addEventListener('popstate', function () {
        choose(fromHash() || defaultChoice(), false);
    });

    if (window.KB4ITFilters) {
        window.KB4ITFilters.extend(tableId, {
            test: function (cell) {
                var p = prefix();
                if (!p) {
                    return true;
                }
                var day = cell ? cell.getAttribute('data-kb-date') || '' : '';
                return day.indexOf(p) === 0;
            },
            chips: function () {
                if (!sel.year) {
                    return [];
                }
                return [{label: label(sel), clear: function () { choose({year: null, month: null, day: null}, true); }}];
            },
            clear: function () { choose({year: null, month: null, day: null}, true); }
        });
    }

    var initial = fromHash() || defaultChoice();
    sel = initial;
    syncView();
    render();
    window.history.replaceState(null, '', '#' + hashOf(sel));
})();
