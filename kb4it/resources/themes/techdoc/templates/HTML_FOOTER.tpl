<!-- FOOTER :: START -->
<div class="kb-footer">
    <a class="kb-footer-top" href="#">&#8593; Back to top</a>
    <span class="kb-footer-meta">Last updated ${var['timestamp']}</span>
</div>
<!-- FOOTER :: END -->
</div><!-- /uk-container -->
</div><!-- /uk-background-muted -->
<!-- CONTENTS (Document) :: END -->
<script>hljs.highlightAll();</script>
<script>
var input = document.getElementById("text_filter");
var filter = document.getElementById("filter");

input.addEventListener( "keyup", function(event)
{
    if ( input.value == "" )
    {
        filter.setAttribute( "uk-filter-control", "" );
    }

    else
    {
        filter.setAttribute( "uk-filter-control", "filter:[data-title*=" + JSON.stringify(input.value) + "i]" );
    }

    filter.click();
});
</script>
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
<script>
(function() {
    document.querySelectorAll(".kb-sect1").forEach(function(sect) {
        var h2 = sect.querySelector("h2.kb-h2");
        var body = sect.querySelector(".kb-section-body");
        if (!h2 || !body) return;
        h2.style.cursor = "pointer";
        h2.addEventListener("click", function() {
            var collapsed = sect.classList.toggle("kb-sect1-collapsed");
            body.style.display = collapsed ? "none" : "";
        });
    });
})();
</script>
<!-- GRID LAYOUT :: END -->
</body>
</html>
