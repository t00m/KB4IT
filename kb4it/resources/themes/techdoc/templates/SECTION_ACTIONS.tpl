<!-- Template SECTION_ACTIONS.tpl :: START -->
% if var['has_toc']:
  % if var['repo']['git']:
        <!-- Edit Button :: START -->
        <li class="uk-link-toggle uk-card uk-card-small uk-card-hover uk-padding-small uk-padding-remove-vertical" uk-tooltip="title: Edit document">
            <a class="uk-link-heading" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}/${var['basename_adoc']}" target="_blank"><span uk-icon="pencil"></span></a>
        </li>
        <!-- Edit Button :: END -->
  % endif
        <!-- Metadata Button :: START -->
        <li class="uk-link-toggle uk-card uk-card-small uk-card-hover uk-padding-small uk-padding-remove-vertical" uk-tooltip="title: Document properties">
            <a class="uk-link-heading" href="#modal-metadata" uk-toggle><span class="uk-link-heading" uk-icon="icon: hashtag; ratio: 1.0;"></span></a>
            <div id="modal-metadata" class="uk-modal-full" uk-modal>
                <div class="uk-modal-dialog">
                    <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                    <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                        <div class="uk-padding-large uk-background-muted">
                            <div class="uk-text-lead uk-text-center uk-text-primary">Metadata</div>
                            <div class="" style="border: 1px solid transparent;">${var['metadata']}</div>
                        </div>
                    </div>
                </div>
            </div>
        </li>
        <!-- Metadata Button :: END -->
        <!-- View Asciidoc Source Button :: START -->
        <li class="uk-link-toggle uk-card uk-card-small uk-card-hover uk-padding-small uk-padding-remove-vertical" uk-tooltip="title: Document source">
            <a class="uk-link-heading" href="#modal-full-source" uk-toggle><span class="uk-link-heading" uk-icon="icon: code; ratio: 1.0;"></span></a>
            <div id="modal-full-source" class="uk-modal-full" uk-modal>
                <div class="uk-modal-dialog">
                    <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                    <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                        <div class="uk-padding-large uk-background-muted">
                            <div class="uk-text-lead uk-text-center uk-text-danger">Source</div>
                            <div class="uk-text-lead">${var['basename_adoc']}&nbsp;<a onclick="copyToClipboard()" class="uk-icon-link uk-margin-small-right uk-link-toggle" uk-icon="copy; ratio: 1.0;" uk-tooltip="title: Copy to clipboard"></a></div>
                            <div class=""><textarea id="source-code" class="uk-width-1-1 uk-height-viewport">${var['source_adoc']}</textarea></div>
                        </div>
                    </div>
                </div>
            </div>
        </li>
        <!-- View Source Button :: END -->
% endif
<!-- Template SECTION_ACTIONS.tpl :: END -->


