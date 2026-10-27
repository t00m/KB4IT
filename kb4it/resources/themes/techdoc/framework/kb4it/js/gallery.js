/* techdoc gallery: choose property values in a dialog, show the matching thumbnails in a masonry grid, enlarge them. */
(function () {
    'use strict';

    var grid = document.getElementById('kb-gal-grid');
    var data = document.getElementById('kb-gal-data');
    if (!grid || !data || typeof UIkit === 'undefined') {
        return;
    }
    data = JSON.parse(data.textContent);
    var docs = data.docs;
    var items = data.items;
    var values = {};  // key -> [[value, images], ...]
    data.filters.forEach(function (group) { values[group.key] = group.values; });

    var status = document.getElementById('kb-gal-status');
    var text = document.getElementById('kb-gal-text');
    var chips = document.getElementById('kb-gal-chips');
    var clear = document.getElementById('kb-gal-clear');
    var modal = document.getElementById('kb-gal-modal');
    var modalTitle = document.getElementById('kb-gal-modal-title');
    var modalFind = document.getElementById('kb-gal-modal-find');
    var modalValues = document.getElementById('kb-gal-modal-values');
    var keyButtons = Array.prototype.slice.call(document.querySelectorAll('.kb-gal-key'));
    var hint = status.textContent;

    var chosen = {};  // key -> [values]; a value of one key widens the choice, keys narrow it
    var openKey = null;
    var shown = [];   // items in the grid, in order, for the lightbox

    function plural(n, one, many) { return n + ' ' + (n === 1 ? one : many); }

    function words() {
        return (text.value || '').toLowerCase().split(/\s+/).filter(Boolean);
    }

    function active() {
        return Object.keys(chosen).length > 0 || words().length > 0;
    }

    function matches(item, skipKey) {
        var props = docs[item.d].props;
        var keys = Object.keys(chosen);
        for (var k = 0; k < keys.length; k++) {
            if (keys[k] === skipKey) {
                continue;
            }
            var have = props[keys[k]] || [];
            if (!chosen[keys[k]].some(function (v) { return have.indexOf(v) >= 0; })) {
                return false;
            }
        }
        var hay = (docs[item.d].title + ' ' + item.caption).toLowerCase();
        return words().every(function (w) { return hay.indexOf(w) >= 0; });
    }

    function el(tag, attrs, textContent) {
        var node = document.createElement(tag);
        Object.keys(attrs || {}).forEach(function (name) { node.setAttribute(name, attrs[name]); });
        if (textContent !== undefined) {
            node.textContent = textContent;
        }
        return node;
    }

    function cell(item, index) {
        var doc = docs[item.d];
        var box = el('div', {'class': 'kb-gal-cell'});
        var card = el('div', {'class': 'kb-gal-card'});
        var zoom = el('a', {'class': 'kb-gal-zoom', href: item.src, 'data-n': String(index),
                            title: item.caption || doc.title});
        var img = el('img', {src: item.thumb, alt: item.caption, loading: 'lazy', decoding: 'async'});
        if (item.w && item.h) {
            img.setAttribute('width', item.w);
            img.setAttribute('height', item.h);
        }
        zoom.appendChild(img);
        card.appendChild(zoom);
        var caption = el('div', {'class': 'kb-gal-cap'});
        caption.appendChild(el('a', {href: doc.href}, doc.title));
        if (item.caption) {
            caption.appendChild(el('span', {'class': 'kb-gal-alt'}, item.caption));
        }
        card.appendChild(caption);
        box.appendChild(card);
        return box;
    }

    function renderGrid() {
        while (grid.firstChild) {
            grid.removeChild(grid.firstChild);
        }
        shown = active() ? items.filter(function (item) { return matches(item, null); }) : [];
        if (!active()) {
            grid.hidden = true;
            status.textContent = hint;
            return;
        }
        var fragment = document.createDocumentFragment();
        shown.forEach(function (item, index) { fragment.appendChild(cell(item, index)); });
        grid.appendChild(fragment);
        grid.hidden = shown.length === 0;
        var docCount = shown.reduce(function (seen, item) { seen[item.d] = 1; return seen; }, {});
        status.textContent = shown.length
            ? plural(shown.length, 'image', 'images') + ' in ' + plural(Object.keys(docCount).length, 'document', 'documents') + '.'
            : 'No image matches these filters.';
        UIkit.update(grid);
    }

    function renderPanel() {
        keyButtons.forEach(function (button) {
            var key = button.getAttribute('data-key');
            var n = (chosen[key] || []).length;
            var info = button.querySelector('.kb-gal-key-info');
            info.textContent = n ? n + ' chosen' : plural(values[key].length, 'value', 'values');
            button.classList.toggle('kb-gal-key-on', n > 0);
        });
        while (chips.firstChild) {
            chips.removeChild(chips.firstChild);
        }
        Object.keys(chosen).forEach(function (key) {
            chosen[key].forEach(function (value) {
                var chip = el('button', {type: 'button', 'class': 'kb-gal-chip', title: 'Remove this filter'});
                chip.appendChild(el('span', {'class': 'kb-gal-chip-key'}, key + ': '));
                chip.appendChild(document.createTextNode(value + ' '));
                chip.appendChild(el('span', {'aria-hidden': 'true'}, '×'));
                chip.addEventListener('click', function () { toggle(key, value, false); });
                chips.appendChild(chip);
            });
        });
        clear.hidden = !active();
    }

    function saveHash() {
        var parts = Object.keys(chosen).map(function (key) {
            return encodeURIComponent(key) + '=' + chosen[key].map(encodeURIComponent).join(',');
        });
        var hash = parts.join('&');
        if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', hash ? '#' + hash : window.location.pathname + window.location.search);
        }
    }

    function loadHash() {
        chosen = {};
        (window.location.hash || '').replace(/^#/, '').split('&').forEach(function (part) {
            var pair = part.split('=');
            var key = decodeURIComponent(pair[0] || '');
            if (!values[key] || !pair[1]) {
                return;
            }
            var known = values[key].map(function (entry) { return entry[0]; });
            var picked = pair[1].split(',').map(decodeURIComponent).filter(function (v) { return known.indexOf(v) >= 0; });
            if (picked.length) {
                chosen[key] = picked;
            }
        });
    }

    function update() {
        renderGrid();
        renderPanel();
        if (openKey) {
            renderValues();
        }
        saveHash();
    }

    function toggle(key, value, on) {
        var list = (chosen[key] || []).filter(function (v) { return v !== value; });
        if (on) {
            list.push(value);
        }
        if (list.length) {
            chosen[key] = list;
        } else {
            delete chosen[key];
        }
        update();
    }

    // The values of the open key, each with the number of images it adds to the other filters.
    function renderValues() {
        var find = (modalFind.value || '').toLowerCase();
        var picked = chosen[openKey] || [];
        while (modalValues.firstChild) {
            modalValues.removeChild(modalValues.firstChild);
        }
        var list = el('ul', {'class': 'kb-gal-values'});
        values[openKey].forEach(function (entry, index) {
            var value = entry[0];
            if (find && value.toLowerCase().indexOf(find) < 0) {
                return;
            }
            var n = items.filter(function (item) {
                return (docs[item.d].props[openKey] || []).indexOf(value) >= 0 && matches(item, openKey);
            }).length;
            var id = 'kb-gal-v' + index;
            var row = el('li', {'class': n === 0 && picked.indexOf(value) < 0 ? 'kb-gal-zero' : ''});
            var box = el('input', {'class': 'uk-checkbox', type: 'checkbox', id: id});
            box.checked = picked.indexOf(value) >= 0;
            box.addEventListener('change', function () { toggle(openKey, value, box.checked); });
            row.appendChild(box);
            row.appendChild(el('label', {'for': id}, value));
            row.appendChild(el('span', {'class': 'kb-gal-n'}, String(n)));
            list.appendChild(row);
        });
        if (!list.firstChild) {
            modalValues.appendChild(el('p', {'class': 'kb-gal-status'}, 'No value matches.'));
        } else {
            modalValues.appendChild(list);
        }
    }

    keyButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            openKey = button.getAttribute('data-key');
            modalTitle.textContent = openKey;
            modalFind.value = '';
            modalFind.parentNode.hidden = values[openKey].length < 12;
            renderValues();
            UIkit.modal(modal).show();
        });
    });
    UIkit.util.on(modal, 'shown', function () {
        if (!modalFind.parentNode.hidden) {
            modalFind.focus();
        }
    });
    UIkit.util.on(modal, 'hidden', function () { openKey = null; });
    modalFind.addEventListener('input', renderValues);
    document.getElementById('kb-gal-modal-none').addEventListener('click', function () {
        delete chosen[openKey];
        update();
    });
    text.addEventListener('input', update);
    clear.addEventListener('click', function () {
        chosen = {};
        text.value = '';
        update();
    });

    // A click opens the lightbox on the shown images, so previous and next follow the filters.
    grid.addEventListener('click', function (event) {
        var link = event.target.closest('a.kb-gal-zoom');
        if (!link || event.ctrlKey || event.metaKey || event.shiftKey) {
            return;
        }
        event.preventDefault();
        var panel = UIkit.lightboxPanel({
            animation: 'fade',
            items: shown.map(function (item) {
                var doc = docs[item.d];
                var caption = el('span');
                if (item.caption) {
                    caption.appendChild(document.createTextNode(item.caption + ' · '));
                }
                caption.appendChild(el('a', {href: doc.href}, doc.title));
                return {source: item.src, type: 'image', caption: caption.outerHTML, alt: item.caption};
            })
        });
        UIkit.util.on(panel.$el, 'hidden', function () { panel.$destroy(true); });
        panel.show(+link.getAttribute('data-n'));
    });

    loadHash();
    update();
}());
