// Renders Mermaid diagrams and KaTeX formulas on the page. Classic script, no modules.
document.addEventListener('DOMContentLoaded', function () {
    if (window.mermaid) {
        var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        mermaid.initialize({startOnLoad: false, theme: dark ? 'dark' : 'default'});
        mermaid.run({querySelector: 'pre.mermaid'});
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
