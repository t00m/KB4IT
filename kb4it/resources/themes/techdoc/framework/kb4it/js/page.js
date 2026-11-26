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
        return hash && !document.getElementById(hash) ? hash : '';
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

/* techdoc document page: "Edit in the editor" opens add.html with the source of the document. */
(function () {
    'use strict';

    document.addEventListener('click', function (event) {
        var link = event.target.closest ? event.target.closest('[data-kb-edit]') : null;
        var source = document.getElementById('source-code');
        if (!link || !source || event.ctrlKey || event.metaKey || event.shiftKey) {
            return;
        }
        event.preventDefault();
        // The text travels in the address: it works from file:// and from a web server, with no storage.
        window.location.href = link.getAttribute('href') + '#edit=' + encodeURIComponent(link.getAttribute('data-kb-edit'))
            + '&text=' + encodeURIComponent(source.value);
    });
}());

/* techdoc document page: focus mode, a switch in the top bar. On, it hides everything but the top bar title,
   the document and the side table of contents (screen.css, .kb-focus) and opens every section. Off, the page
   is back as it was, with each section open or folded as before. */
(function () {
    'use strict';

    var button = document.querySelector('[data-kb-focus]');
    if (!button) {
        return;
    }
    var root = document.documentElement;
    var content = document.querySelector('.kb-content');
    var sections = content ? Array.prototype.slice.call(content.querySelectorAll('.kb-sect1, .kb-sect2, .kb-sect3, .kb-sect4')) : [];
    var folded = [];

    function setFolded(section, closed) {
        section.classList.toggle('kb-closed', closed);
        var heading = section.firstElementChild;
        if (heading && heading.classList.contains('kb-fold-toggle')) {
            heading.setAttribute('aria-expanded', String(!closed));
        }
    }

    // The first heading in view, and where it is, so the reader keeps their place when the page changes.
    function headingInView() {
        var headings = content ? content.querySelectorAll('h2, h3, h4, h5') : [];
        for (var i = 0; i < headings.length; i++) {
            var top = headings[i].getBoundingClientRect().top;
            if (headings[i].offsetParent && top >= 0) {
                return {heading: headings[i], top: top};
            }
        }
        return null;
    }

    function setFocus(on) {
        var place = window.scrollY > 0 ? headingInView() : null;
        if (on) {
            folded = sections.filter(function (s) { return s.classList.contains('kb-closed'); });
        }
        sections.forEach(function (s) { setFolded(s, !on && folded.indexOf(s) >= 0); });
        root.classList.toggle('kb-focus', on);
        button.setAttribute('aria-pressed', String(on));
        var label = on ? 'Leave focus mode' : 'Focus mode';
        button.setAttribute('title', label);
        button.setAttribute('aria-label', label);
        if (place) {
            window.scrollBy(0, place.heading.getBoundingClientRect().top - place.top);
        }
    }

    button.addEventListener('click', function (event) {
        event.preventDefault();
        setFocus(!root.classList.contains('kb-focus'));
    });
}());
