<!-- FOOTER :: START -->
<div class="kb-footer">
    <a class="kb-footer-top" href="#">↑ Back to top</a>
    <span class="kb-footer-meta">Last updated ${var['timestamp']}</span>
</div>
<!-- FOOTER :: END -->
</div><!-- /uk-container -->
</div><!-- /uk-background-muted -->
<!-- CONTENTS (Document) :: END -->
<script>hljs.highlightAll();</script>
<script>
var input = document.getElementById('text_filter');
var filter = document.getElementById('filter');

input.addEventListener( 'keyup', function(event)
{
    if ( input.value == "" )
    {
        filter.setAttribute( 'uk-filter-control', '' );
    }

    else
    {
        filter.setAttribute( 'uk-filter-control', 'filter:[data-title*=\'' + input.value + '\'i]' );
    }

    filter.click();
});
</script>
<script>
function copyToClipboard() {
  var copyText = document.getElementById("source-code");
  copyText.select();
  copyText.setSelectionRange(0, 99999)
  document.execCommand("copy");
  alert("Text copied to clipboard");
}
</script>
<!-- GRID LAYOUT :: END -->
</body>
</html>
