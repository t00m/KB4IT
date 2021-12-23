            <div class="uk-navbar-center">
                <!-- DOCUMENT TITLE :: START -->
                <ul class="uk-navbar-nav">
                    <li uk-tooltip="title: Edit document">
                        <a class="uk-card uk-card-hover uk-button uk-card uk-card-hover uk-border-rounded uk-link-heading uk-padding" href="https://${var['theme']['git_server']}/${var['theme']['git_user']}/${var['theme']['git_repo']}/edit/${var['theme']['git_branch']}/${var['theme']['git_path']}/${var['basename']}" target="_blank">
                            <span class="uk-text-bold uk-text-primary uk-text-truncate" uk-icon="icon: file-edit; ratio: 1">${var['title']}</span>
                        </a>
                    </li>
                </ul>
                <!-- DOCUMENT TITLE :: END -->
            </div>
            <div class="uk-navbar-right noprint">
                <ul class="uk-navbar-nav">
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="javascript:location.reload();"><span uk-icon="refresh"></span></a>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="#">About</a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="about_app.html"><span class="uk-padding-small">About this app</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="about_theme.html"><span class="uk-padding-small">About this theme</span></a>
                                </li>
                                <li class="uk-nav-divider"></li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="about_kb4it.html"><span class="uk-padding-small">About KB4IT</span></a>
                                </li>
                            </ul>
                        </div>
                    </li>
                </ul>
            </div>
        </nav>
    </div>
</div>
<div class="uk-container uk-container-center">
