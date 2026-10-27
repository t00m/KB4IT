/* techdoc gallery: filter the images by the properties of their documents, enlarge them in a lightbox. */
(function () {
    'use strict';

    var grid = document.getElementById('kb-gal-grid');
    var data = document.getElementById('kb-gal-data');
    if (!grid || !data) {
        return;
    }
    var items = JSON.parse(data.textContent).items;
    var cells = Array.prototype.slice.call(grid.querySelectorAll('.kb-gal-cell'));
    var boxes = Array.prototype.slice.call(document.querySelectorAll('.kb-gal-values input[type=checkbox]'));
    var text = document.getElementById('kb-gal-text');
    var count = document.getElementById('kb-gal-count');
    var none = document.getElementById('kb-gal-none');

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, function (c) {
            return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c];
        });
    }

    // {key: [values]} of the checked boxes; values of one key widen the choice, keys narrow it.
    function selected() {
        var chosen = {};
        boxes.forEach(function (box) {
            if (box.checked) {
                (chosen[box.getAttribute('data-key')] = chosen[box.getAttribute('data-key')] || []).push(box.value);
            }
        });
        return chosen;
    }

    function matches(item, chosen, words, skipKey) {
        var keys = Object.keys(chosen);
        for (var k = 0; k < keys.length; k++) {
            if (keys[k] === skipKey) {
                continue;
            }
            var have = item.props[keys[k]] || [];
            if (!chosen[keys[k]].some(function (v) { return have.indexOf(v) >= 0; })) {
                return false;
            }
        }
        var hay = (item.title + ' ' + item.caption).toLowerCase();
        return words.every(function (w) { return hay.indexOf(w) >= 0; });
    }

    function apply() {
        var chosen = selected();
        var words = (text.value || '').toLowerCase().split(/\s+/).filter(Boolean);
        var shown = 0;
        cells.forEach(function (cell) {
            var ok = matches(items[+cell.getAttribute('data-i')], chosen, words, null);
            cell.hidden = !ok;
            shown += ok ? 1 : 0;
        });
        // Each value counts the images it would show with the other filters kept.
        boxes.forEach(function (box) {
            var key = box.getAttribute('data-key');
            var n = 0;
            items.forEach(function (item) {
                if ((item.props[key] || []).indexOf(box.value) >= 0 && matches(item, chosen, words, key)) {
                    n += 1;
                }
            });
            var badge = box.parentNode.querySelector('.kb-gal-n');
            badge.textContent = n;
            box.parentNode.classList.toggle('kb-gal-zero', n === 0 && !box.checked);
        });
        var noun = items.length === 1 ? ' image' : ' images';
        count.textContent = shown === items.length ? items.length + noun : shown + ' of ' + items.length + noun;
        none.hidden = shown > 0;
    }

    boxes.forEach(function (box) { box.addEventListener('change', apply); });
    text.addEventListener('input', apply);
    document.getElementById('kb-gal-clear').addEventListener('click', function () {
        boxes.forEach(function (box) { box.checked = false; });
        text.value = '';
        apply();
    });

    // A click opens the lightbox on the images that are shown, so previous and next follow the filters.
    grid.addEventListener('click', function (event) {
        var link = event.target.closest('a.kb-gal-zoom');
        if (!link || typeof UIkit === 'undefined' || event.ctrlKey || event.metaKey || event.shiftKey) {
            return;
        }
        event.preventDefault();
        var visible = cells.filter(function (cell) { return !cell.hidden; });
        var start = visible.indexOf(link.closest('.kb-gal-cell'));
        var panel = UIkit.lightboxPanel({
            animation: 'fade',
            items: visible.map(function (cell) {
                var item = items[+cell.getAttribute('data-i')];
                var caption = (item.caption ? escapeHtml(item.caption) + ' &middot; ' : '')
                    + '<a href="' + escapeHtml(item.href) + '">' + escapeHtml(item.title) + '</a>';
                return {source: item.src, type: 'image', caption: caption, alt: item.caption};
            })
        });
        // A new panel per click; remove it once closed.
        UIkit.util.on(panel.$el, 'hidden', function () { panel.$destroy(true); });
        panel.show(Math.max(start, 0));
    });
}());
