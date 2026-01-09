                </div>
                <!-- Sidebar Column :: START-->
                <div class="uk-width-1-3@m" uk-height-viewport="expand: true">
                  <div class="uk-sticky" uk-sticky="offset: 40">
                    <h2 class="uk-heading-line uk-text-center"><a class="uk-link-toggle" href="index.html"><span class="uk-link-heading">${var['repo']['title']}</span></a></h2>
<div class="uk-card uk-card-body uk-card-small uk-flex uk-flex-top uk-flex-center">
<blockquote>
<p class="uk-text-center">${var['repo']['tagline']}</p>
</blockquote>
</div>

                      <div class="sidebar">
<!--
                      <h5 class="sidebar-title">About</h5>
                      <p class="uk-text-small">${var['repo']['tagline']}</p>
-->
<div class="uk-card uk-card-body uk-card-small uk-flex uk-flex-top uk-flex-center">
<ul class="uk-iconnav">
    <li>
        <a href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/new/${var['repo']['git_branch']}/${var['repo']['git_path']}" uk-icon="icon: plus" uk-tooltip="Create new post" target="_blank"></a>
    </li>
    <li><a href="all.html" uk-icon="icon: list" uk-tooltip="Documents"></a></li>
    <li><a href="bookmarks.html" uk-icon="icon: star" uk-tooltip="Bookmarks"></a></li>
    <li><a href="events.html" uk-icon="icon: calendar" uk-tooltip="Events"></a></li>
    <li><a href="properties.html" uk-icon="icon: world" uk-tooltip="Properties"></a></li>
</ul>
</div>

                      <div class="uk-text-center uk-card uk-card-body uk-card-big">
                        <hr class="uk-divider-icon">
                        <span class="uk-text-small uk-text-muted">Blog updated on<br/>${var['repo']['updated']}</span>
                        <p>
                            <span class="uk-link">
                                <a href="https://github.com/t00m/KB4IT" target="_blank">
                                    <img src="resources/common/images/kb4it-badge-built-with.svg">
                                </a>
                            </span>
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- Sidebar Column :: END-->
            </div>
            <!-- Main Content Column :: END-->
        </div>
        <!-- GRID :: END -->
    </div>
    <!-- Blog container :: END -->
<script>hljs.highlightAll();</script>
<script>
<!-- Necessary javascript for filtering results -->
<!-- Hack found in: https://codepen.io/acidrums4/pen/GBpYbO -->
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
</body>
</html>
