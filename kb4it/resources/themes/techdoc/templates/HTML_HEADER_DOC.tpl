            <div class="uk-navbar-center">
                <!-- DOCUMENT TITLE :: START -->
                <ul class="uk-navbar-nav">
                    <li uk-tooltip="title: Edit document">
                        <a class="uk-card uk-card-small uk-card-hover uk-button uk-card uk-card-small uk-card-hover uk-border-rounded uk-link-heading uk-padding" href="https://${var['theme']['git_server']}/${var['theme']['git_user']}/${var['theme']['git_repo']}/edit/${var['theme']['git_branch']}/${var['theme']['git_path']}/${var['basename']}" target="_blank">
                            <span class="uk-text-bold uk-text-primary uk-text-truncate" uk-icon="icon: file-edit; ratio: 1">${var['title']}</span>
                        </a>
                    </li>
                    <li>
                       <a href="#"><span class="uk-text-primary uk-text-small uk-text-truncate">${var['title']}</span></a><!-- ${var['basename']} -->
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li>
                                    <!-- View Metadata Button :: START -->
                                    <a class="uk-button uk-card uk-card-small uk-card-hover uk-button uk-card uk-card-small uk-card-hover uk-border-rounded uk-link-heading" href="#modal-full-metadata" uk-toggle><span class="">Metadata</span></a>
                                    <div id="modal-full-metadata" class="uk-modal-full" uk-modal>
                                        <div class="uk-modal-dialog">
                                            <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                                            <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                                                <div class="uk-padding-large uk-background-muted">
                                                    <div class="uk-text-lead uk-text-center uk-text-danger">Meta</div>
<!-- METADATA :: START -->
${var['meta_section']}
<!-- METADATA :: END -->
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <!-- View Metadata Button :: END -->
                                </li>
                                <li>
                                    <!-- View Asciidoc Source Button :: START -->
                                    <a class="uk-button uk-card uk-card-small uk-card-hover uk-button uk-card uk-card-small uk-card-hover uk-border-rounded uk-link-heading" href="#modal-full-source" uk-toggle><span class="">Source</span></a>
                                    <div id="modal-full-source" class="uk-modal-full" uk-modal>
                                        <div class="uk-modal-dialog">
                                            <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                                            <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                                                <div class="uk-padding-large uk-background-muted">
                                                    <div class="uk-text-lead uk-text-center uk-text-danger">Source</div>
                                                    <div class="uk-text-lead" uk-tooltip="title: Copy to clipboard">${var['basename']}&nbsp;<a onclick="copyToClipboard()" class="uk-icon-link uk-margin-small-right" uk-icon="copy"></a></div>
                                                    <textarea id="source-code" class="uk-width-1-1 uk-height-viewport">${var['source_code']}</textarea>
                                                </div>
                                            </div>
                                        </div>
                                    </div> <!-- View Source Button :: END -->
                                </li>
                            </ul>
                        </div>
                    </li>
                </u>
                <!-- DOCUMENT TITLE :: END -->
            </div>
            <div class="uk-navbar-right noprint">
                <ul class="uk-navbar-nav">
                    <li>
                        <a class="uk-button uk-card uk-card-small uk-card-hover uk-link-heading" href="#">About</a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-small uk-card-hover uk-border-rounded uk-link-heading" href="about_app.html"><span class="uk-padding-none">About this app</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-small uk-card-hover uk-border-rounded uk-link-heading" href="about_theme.html"><span class="uk-padding-none">About this theme</span></a>
                                </li>
                                <li class="uk-nav-divider"></li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-small uk-card-hover uk-border-rounded uk-link-heading" href="about_kb4it.html"><span class="uk-padding-none">About KB4IT</span></a>
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
