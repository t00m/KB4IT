/* techdoc document page: the info card opens, closes and remembers its tab. */
(function () {
    'use strict';

    var card = document.getElementById('kb-info-card');
    if (!card || typeof UIkit === 'undefined') {
        return;
    }
    var tabs = card.querySelector('[data-uk-tab]');
    var toggle = card.querySelector('.kb-info-toggle');
    var page = window.location.pathname.split('/').pop() || 'index.html';
    var TAB_KEY = 'kb-info-card-tab';
    var OPEN_KEY = 'kb-info-card:' + page;
    // A document without a Summary is rendered open and always starts on Details.
    var openByDefault = card.classList.contains('kb-open');

    function load(key) {
        try { return window.localStorage.getItem(key); } catch (e) { return null; }
    }

    function save(key, value) {
        try { window.localStorage.setItem(key, value); } catch (e) { /* private window: not kept */ }
    }

    function names() {
        return Array.prototype.map.call(tabs.children, function (li) { return li.getAttribute('data-kb-tab'); });
    }

    function setOpen(open, remember) {
        card.classList.toggle('kb-open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (remember) {
            save(OPEN_KEY, open ? '1' : '0');
        }
    }

    function show(name) {
        var index = names().indexOf(name);
        if (index >= 0) {
            UIkit.tab(tabs).show(index);
        }
    }

    // #kb-info-details opens the card on Details; #details does too, unless the page has
    // its own element with that id (a section heading), which keeps the link.
    function tabFromHash() {
        var hash = window.location.hash.replace('#', '');
        if (hash.indexOf('kb-info-') === 0) {
            return hash.slice('kb-info-'.length);
        }
        return document.getElementById(hash) ? '' : hash;
    }

    function fromHash() {
        var name = tabFromHash();
        if (names().indexOf(name) >= 0) {
            setOpen(true, false);
            show(name);
            card.scrollIntoView({block: 'start'});
        }
    }

    var stored = load(OPEN_KEY);
    if (stored !== null) {
        setOpen(stored === '1', false);
    }
    if (!openByDefault && load(TAB_KEY)) {
        show(load(TAB_KEY));
    }
    fromHash();

    toggle.addEventListener('click', function () {
        setOpen(!card.classList.contains('kb-open'), true);
    });

    // Runs before UIkit's own handler: a click on the open tab closes the card, any tab opens it.
    tabs.addEventListener('click', function (event) {
        var li = event.target.closest('li');
        if (!li || !tabs.contains(li)) {
            return;
        }
        if (card.classList.contains('kb-open') && li.classList.contains('uk-active')) {
            event.preventDefault();
            event.stopPropagation();
            setOpen(false, true);
            return;
        }
        save(TAB_KEY, li.getAttribute('data-kb-tab'));
        setOpen(true, true);
    }, true);

    window.addEventListener('hashchange', fromHash);
})();
