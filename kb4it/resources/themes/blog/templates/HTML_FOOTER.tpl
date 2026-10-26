        </div>
        <!-- CONTENT COLUMN :: END -->
        <!-- SIDEBAR :: START -->
        <aside class="uk-width-1-4@m" data-uk-height-viewport="expand: true">
            <div class="uk-sticky" data-uk-sticky="offset: 40">
                <!-- SITE TITLE :: START -->
                <h2 class="uk-heading-line uk-text-center uk-margin-remove">
                    <a class="uk-link-toggle" href="index.html">
                        <span class="uk-link-heading">${var['repo']['title']}</span>
                    </a>
                </h2>
                <!-- SITE TITLE :: END -->
% if var.get('search_box'):
                <!-- SEARCH BOX :: START -->
                <div class="uk-flex uk-flex-center uk-margin-small">${var['search_box'] | n}</div>
                <!-- SEARCH BOX :: END -->
% endif
                <!-- TAGLINE :: START -->
                <div class="uk-flex uk-flex-top uk-flex-center uk-margin">
                    <blockquote>
                        <p class="uk-text-center">${var['repo']['tagline']}</p>
                    </blockquote>
                </div>
                <!-- TAGLINE :: END -->
                <!-- SITE MENU :: START -->
                <nav class="uk-card uk-card-body uk-card-small uk-flex uk-flex-top uk-flex-left" aria-label="Site">
                    <ul class="uk-list uk-text-left uk-margin-left">
% if var.get('git_ok'):
                        <li>
                            <span data-uk-icon="icon: plus" data-uk-tooltip="Create new post"></span>
                            <a class="uk-link-heading" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/new/${var['repo']['git_branch']}/${var['repo']['git_path']}" target="_blank">
                                <span class="uk-link-toogle uk-margin-left">Create new post</span>
                            </a>
                        </li>
% endif
% if var['editor']:
                        <li>
                            <span data-uk-icon="icon: plus-circle" data-uk-tooltip="Add document"></span>
                            <a class="uk-link-heading" href="add.html">
                                <span class="uk-link-toogle uk-margin-left">Add document</span>
                            </a>
                        </li>
% endif
                        <li>
                            <span data-uk-icon="icon: list" data-uk-tooltip="All posts"></span>
                            <a class="uk-link-heading" href="all.html">
                                <span class="uk-link-toogle uk-margin-left">All documents</span>
                            </a>
                        </li>
                        <li>
                            <span data-uk-icon="icon: star" data-uk-tooltip="Bookmarks"></span>
                            <a class="uk-link-heading" href="bookmarks.html">
                                <span class="uk-link-toogle uk-margin-left">Bookmarks</span>
                            </a>
                        </li>
                        <li>
                            <span data-uk-icon="icon: world" data-uk-tooltip="Browse by metadata"></span>
                            <a class="uk-link-heading" href="properties.html">
                                <span class="uk-link-toogle uk-margin-left">Metadata</span>
                            </a>
                        </li>
                        <li>
                            <span data-uk-icon="icon: calendar" data-uk-tooltip="Posts by year"></span>
                            <a class="uk-link-heading" href="events.html">
                                <span class="uk-link-toogle uk-margin-left">Archive</span>
                            </a>
                        </li>
                        <li class="uk-nav-divider"></li>
                        <li>
                            <span data-uk-icon="icon: info" data-uk-tooltip="About"></span>
                            <a class="uk-link-heading" href="about_app.html">
                                <span class="uk-link-toogle uk-margin-left">About</span>
                            </a>
                        </li>
                    </ul>
                </nav>
                <!-- SITE MENU :: END -->
                <!-- FOOTER :: START -->
                <footer class="uk-text-center uk-card uk-card-body uk-card-big">
                    <hr class="uk-divider-icon">
                    <p>
                        <a href="about_kb4it.html">
                            <img src="resources/common/images/kb4it-badge-built-with.svg" alt="Built with KB4IT">
                        </a>
                    </p>
                </footer>
                <!-- FOOTER :: END -->
            </div>
        </aside>
        <!-- SIDEBAR :: END -->
    </div>
</div>
<!-- PAGE :: END -->
<!-- PAGE SCRIPTS :: START -->
% if (var['repo'].get('markdown') or {}).get('highlight', 'client') == 'client':
<!-- Code highlighting -->
<script>hljs.highlightAll();</script>
% endif
<!-- PAGE SCRIPTS :: END -->
</body>
</html>
