// Renders Mermaid diagrams and KaTeX formulas on the page. Classic script, no modules.
(function () {
    // A diagram is not code: the theme's pre background, border and padding must not frame it.
    var style = document.createElement('style');
    style.textContent = 'pre.mermaid{background:transparent!important;border:0!important;' +
        'padding:0!important;box-shadow:none!important;color:inherit!important;}';
    document.head.appendChild(style);

    // True when the first opaque background from body up is dark; light when none is found.
    function pageIsDark() {
        for (var el = document.body; el; el = el.parentElement) {
            var rgb = getComputedStyle(el).backgroundColor.match(/^rgba?\(([^)]*)\)/);
            if (!rgb) { continue; }
            var c = rgb[1].split(/[\s,\/]+/).map(parseFloat);
            if (c.length > 3 && c[3] === 0) { continue; }
            return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255 < 0.5;
        }
        return false;
    }

    function renderDiagrams(nodes) {
        mermaid.run({nodes: nodes, suppressErrors: true}).catch(function () {});
    }

    // Mermaid needs a layout box to measure text. A diagram inside a collapsed section or
    // an inactive tab (display: none) fails with "Syntax error in text", so it waits until
    // it is shown.
    function renderMermaid() {
        var shown = [], hidden = [];
        document.querySelectorAll('pre.mermaid').forEach(function (el) {
            (el.getClientRects().length ? shown : hidden).push(el);
        });
        if (shown.length) { renderDiagrams(shown); }
        if (!hidden.length) { return; }
        if (!window.ResizeObserver) { renderDiagrams(hidden); return; }
        var observer = new ResizeObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.target.getClientRects().length) {
                    observer.unobserve(entry.target);
                    renderDiagrams([entry.target]);
                }
            });
        });
        hidden.forEach(function (el) { observer.observe(el); });
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (window.mermaid) {
            mermaid.initialize({startOnLoad: false, theme: pageIsDark() ? 'dark' : 'default'});
            renderMermaid();
        }
        if (window.katex) {
            document.querySelectorAll('.kb4it-math').forEach(function (el) {
                katex.render(el.textContent, el, {
                    displayMode: el.classList.contains('kb4it-math-display'),
                    throwOnError: false
                });
            });
        }
    });
})();
