% if not var['SystemPage']:
  % if var.get('git_ok'):
        <!-- EDIT BUTTON :: START -->
        <a class="kb4it-page-action" data-uk-tooltip="title: Edit document" aria-label="Edit document" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}/${var['basename_md']}" target="_blank"><span data-uk-icon="pencil"></span></a>
        <!-- EDIT BUTTON :: END -->
  % endif
        <!-- PROPERTIES BUTTON :: START -->
        <a class="kb4it-page-action" href="#kb-info-details" data-uk-tooltip="title: Document properties" aria-label="Document properties"><span data-uk-icon="icon: hashtag; ratio: 1.0;"></span></a>
        <!-- PROPERTIES BUTTON :: END -->
  % if var.get('has_quality'):
        <!-- QUALITY BUTTON :: START -->
        <a class="kb4it-page-action" href="#kb-info-quality" data-uk-tooltip="title: Document quality" aria-label="Document quality"><span data-uk-icon="icon: star; ratio: 1.0;"></span></a>
        <!-- QUALITY BUTTON :: END -->
  % endif
        <!-- SOURCE BUTTON AND DIALOG :: START -->
        <a class="kb4it-page-action" href="#modal-full-source" data-uk-toggle data-uk-tooltip="title: Document source" aria-label="Document source"><span data-uk-icon="icon: code; ratio: 1.0;"></span></a>
            <div id="modal-full-source" class="uk-modal-full" data-uk-modal>
                <div class="uk-modal-dialog uk-height-viewport">
                    <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" data-uk-close></button>
                    <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" data-uk-grid>
                        <div class="uk-padding-large uk-background-muted">
                            <div class="uk-text-lead uk-text-center uk-text-danger">Source</div>
                            <div class="uk-text-lead">${var['basename_md']}&nbsp;<a onclick="copyToClipboard()" class="uk-icon-link uk-margin-small-right uk-link-toggle" data-uk-icon="icon: copy; ratio: 1.0" data-uk-tooltip="title: Copy to clipboard"></a></div>
                            <div class=""><textarea id="source-code" class="uk-width-1-1 uk-height-viewport">${var['source_md']}</textarea></div>
                        </div>
                    </div>
                </div>
            </div>
        <!-- SOURCE BUTTON AND DIALOG :: END -->
        <!-- PRINT BUTTON :: START -->
        <a class="kb4it-page-action" href="javascript:window.print()" data-uk-tooltip="title: Print document" aria-label="Print document"><span data-uk-icon="icon: print; ratio: 1.0;"></span></a>
        <!-- PRINT BUTTON :: END -->
% endif


