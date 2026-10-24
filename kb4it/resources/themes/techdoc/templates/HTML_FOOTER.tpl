<!-- FOOTER :: START -->
<footer class="kb-footer">
    <a class="kb-footer-top" href="#">&#8593; Back to top</a>
    <span class="kb-footer-meta">Last updated ${var['timestamp']}</span>
</footer>
<!-- FOOTER :: END -->
</div>
<!-- CONTENT :: END -->
</div>
<!-- PAGE :: END -->
<!-- PAGE SCRIPTS :: START -->
% if (var['repo'].get('markdown') or {}).get('highlight', 'client') == 'client':
<!-- Code highlighting -->
<script>hljs.highlightAll();</script>
% endif
<!-- Copy the document source to the clipboard (source dialog) -->
<script>
function copyToClipboard() {
  var el = document.getElementById("source-code");
  el.select();
  el.setSelectionRange(0, 99999);
  navigator.clipboard.writeText(el.value).catch(function() {
    document.execCommand("copy");
  });
  UIkit.notification({message: "Source copied to clipboard", status: "success", timeout: 2000});
}
</script>
<!-- Section folding -->
<script>
// Every section folds when you click its heading. Every section starts folded except the first
// top-level one and the sections inside it. A link to a section unfolds it and the sections around it.
(function() {
    var content = document.querySelector('.kb-content');
    if (!content) return;
    var SECT = '.kb-sect1, .kb-sect2, .kb-sect3, .kb-sect4';
    var sects = Array.from(content.querySelectorAll(SECT)).filter(function(s) {
        return s.querySelector(':scope > .kb-section-body');
    });
    if (!sects.length) return;
    var top = sects.filter(function(s) { return s.classList.contains('kb-sect1'); });
    var first = top[0] || sects[0];
    sects.forEach(function(s) {
        if (s !== first && !first.contains(s)) s.classList.add('kb-closed');
    });
    sects.forEach(function(s) {
        var heading = s.firstElementChild;
        if (!heading || !/^H[2-5]$/.test(heading.tagName)) return;
        heading.classList.add('kb-fold-toggle');
        heading.setAttribute('role', 'button');
        heading.setAttribute('tabindex', '0');
        function sync() { heading.setAttribute('aria-expanded', String(!s.classList.contains('kb-closed'))); }
        function toggle() { s.classList.toggle('kb-closed'); sync(); }
        heading.addEventListener('click', toggle);
        heading.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
        });
        sync();
    });
    function reveal(id) {
        var target = id && document.getElementById(id);
        if (!target || !content.contains(target)) return;
        for (var node = target; node && node !== content; node = node.parentElement) {
            if (node.matches && node.matches(SECT) && node.classList.contains('kb-closed')) {
                node.classList.remove('kb-closed');
                var h = node.firstElementChild;
                if (h) h.setAttribute('aria-expanded', 'true');
            }
        }
        target.scrollIntoView();
    }
    function fromHash() { try { reveal(decodeURIComponent(location.hash.slice(1))); } catch (e) {} }
    window.addEventListener('hashchange', fromHash);
    document.addEventListener('click', function(e) {
        var a = e.target.closest && e.target.closest('a[href^="#"]');
        if (a && a.getAttribute('href').length > 1 && !a.hasAttribute('data-uk-toggle')) {
            // A click on the current hash fires no hashchange, so reveal it here too.
            setTimeout(function() { reveal(decodeURIComponent(a.getAttribute('href').slice(1))); }, 0);
        }
    });
    fromHash();
})();
</script>
<!-- PAGE SCRIPTS :: END -->
</body>
</html>
