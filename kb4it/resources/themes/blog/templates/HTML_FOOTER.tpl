                </div>
                <!-- Sidebar Column :: START-->
                <div class="uk-width-1-4@m" uk-height-viewport="expand: true">
                  <div class="uk-sticky" uk-sticky="offset: 40">
                    <h2 class="uk-heading-line uk-text-center uk-margin-remove">
                        <a class="uk-link-toggle" href="index.html">
                        <span class="uk-link-heading">${var['repo']['title']}</span>
                        </a>
                    </h2>
                    <div class="uk-flex uk-flex-top uk-flex-center uk-margin">
            <blockquote>
            <p class="uk-text-center">${var['repo']['tagline']}</p>
            </blockquote>
            </div>

        <div class="uk-card uk-card-body uk-card-small uk-flex uk-flex-top uk-flex-left">
        <ul class="uk-list uk-text-left uk-margin-left">
                <li>
                    <span uk-icon="icon: plus" uk-tooltip="Create new post"></span>
                    <a class="uk-link-heading" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/new/${var['repo']['git_branch']}/${var['repo']['git_path']}" target="_blank">
                        <span class="uk-link-toogle uk-margin-left">Create new post</span>
                    </a>
                </li>
                <li>
                    <span uk-icon="icon: list" uk-tooltip="All posts"></span>
                    <a class="uk-link-heading" href="all.html">
                        <span class="uk-link-toogle uk-margin-left">All documents</span>
                    </a>
                </li>
                <li>
                    <span uk-icon="icon: star" uk-tooltip="Bookmarks"></span>
                    <a class="uk-link-heading" href="bookmarks.html">
                        <span class="uk-link-toogle uk-margin-left">Bookmarks</span>
                    </a>
                </li>
                <li>
                    <span uk-icon="icon: calendar" uk-tooltip="Posts by date"></span>
                    <a class="uk-link-heading" href="events.html">
                        <span class="uk-link-toogle uk-margin-left">Posts by date</span>
                    </a>
                </li>
                <li>
                    <span uk-icon="icon: world" uk-tooltip="Browse by metadata"></span>
                    <a class="uk-link-heading" href="properties.html">
                        <span class="uk-link-toogle uk-margin-left">Browse by metadata</span>
                    </a>
                </li>
        </ul>
    </div>

                      <div class="uk-text-center uk-card uk-card-body uk-card-big">
                        <hr class="uk-divider-icon">
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
