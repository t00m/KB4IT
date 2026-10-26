/* techdoc content blocks: copy code, fold long code, back to top and notes for print. */
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

    // A closed note prints as if it were open; the screen state comes back after printing.
    var closed = [];
    window.addEventListener('beforeprint', function () {
        closed = Array.prototype.filter.call(
            document.querySelectorAll('.kb-content details'), function (note) { return !note.open; });
        closed.forEach(function (note) { note.open = true; });
    });
    window.addEventListener('afterprint', function () {
        closed.forEach(function (note) { note.open = false; });
        closed = [];
    });
})();
