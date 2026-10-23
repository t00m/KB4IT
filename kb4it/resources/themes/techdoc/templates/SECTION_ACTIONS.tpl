<!-- Template SECTION_ACTIONS.tpl :: START -->
% if not var['SystemPage']:
  % if var.get('git_ok'):
        <!-- Edit Button :: START -->
        <a class="kb4it-page-action" uk-tooltip="title: Edit document" aria-label="Edit document" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}/${var['basename_md']}" target="_blank"><span uk-icon="pencil"></span></a>
        <!-- Edit Button :: END -->
  % endif
        <!-- Metadata Button :: START -->
        <a class="kb4it-page-action" href="#modal-metadata" uk-toggle uk-tooltip="title: Document properties" aria-label="Document properties"><span uk-icon="icon: hashtag; ratio: 1.0;"></span></a>
            <div id="modal-metadata" class="uk-modal-full" uk-modal>
                <div class="uk-modal-dialog uk-height-viewport">
                    <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                    <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                        <div class="uk-padding-large uk-background-muted">
                            <div class="uk-text-lead uk-text-center uk-text-primary">Metadata</div>
                            <div class="" style="border: 1px solid transparent;">${var['metadata'] | n}</div>
                        </div>
                    </div>
                </div>
            </div>
        <!-- Metadata Button :: END -->
        <!-- View Markdown Source Button :: START -->
        <a class="kb4it-page-action" href="#modal-full-source" uk-toggle uk-tooltip="title: Document source" aria-label="Document source"><span uk-icon="icon: code; ratio: 1.0;"></span></a>
            <div id="modal-full-source" class="uk-modal-full" uk-modal>
                <div class="uk-modal-dialog uk-height-viewport">
                    <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                    <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                        <div class="uk-padding-large uk-background-muted">
                            <div class="uk-text-lead uk-text-center uk-text-danger">Source</div>
                            <div class="uk-text-lead">${var['basename_md']}&nbsp;<a onclick="copyToClipboard()" class="uk-icon-link uk-margin-small-right uk-link-toggle" uk-icon="icon: copy; ratio: 1.0" uk-tooltip="title: Copy to clipboard"></a></div>
                            <div class=""><textarea id="source-code" class="uk-width-1-1 uk-height-viewport">${var['source_md']}</textarea></div>
                        </div>
                    </div>
                </div>
            </div>
        <!-- View Source Button :: END -->
        <!-- Print Button :: START -->
        <a class="kb4it-page-action" href="javascript:window.print()" uk-tooltip="title: Print document" aria-label="Print document"><span uk-icon="icon: print; ratio: 1.0;"></span></a>
        <!-- Print Button :: END -->
% endif
<!-- Template SECTION_ACTIONS.tpl :: END -->


