<!-- Template SECTION_ACTIONS.tpl :: START -->
% if var['has_toc']:
  % if var['repo']['git']:
        <li class="uk-link-toggle uk-button uk-button-default uk-button-small uk-width-1-1 uk-border-rounded uk-margin-small"><!-- Edit Button :: START -->
            <a class="uk-link-heading" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}/${var['basename_adoc']}" target="_blank"><div class="uk-grid-medium uk-flex-middle" uk-grid><div class="uk-width-auto uk-padding-remove-top uk-padding-remove-bottom"><span class="uk-link-heading" uk-icon="icon: pencil; ratio: 1.0;"></span></div><div class="uk-width-auto uk-padding-small uk-padding-remove-top uk-padding-remove-bottom">Edit</div></div></a>
        </li><!-- Edit Button :: END -->
  % endif
        <li class="uk-link-toggle uk-button uk-button-default uk-button-small uk-width-1-1 uk-border-rounded uk-margin-small"><!-- Print Button :: START -->
            <a class="uk-link-heading"  onclick="window.print()"><div class="uk-grid-medium uk-flex-middle" uk-grid><div class="uk-width-auto uk-padding-remove-top uk-padding-remove-bottom"><span class="uk-link-heading" uk-icon="icon: print; ratio: 1.0;"></span></div><div class="uk-width-auto uk-padding-small uk-padding-remove-top uk-padding-remove-bottom">Print</div></div></a>
        </li><!-- Print Button :: END -->
        <li class="uk-link-toggle uk-button uk-button-default uk-button-small uk-width-1-1 uk-border-rounded uk-margin-small"><!-- Metadata Button :: START -->
            <a class=""uk-link-heading"" href="#modal-metadata" uk-toggle><div class="uk-grid-medium uk-flex-middle" uk-grid><div class="uk-width-auto uk-padding-remove-top uk-padding-remove-bottom"><span class="uk-link-heading" uk-icon="icon: hashtag; ratio: 1.0;"></span></div><div class="uk-width-auto uk-padding-small uk-padding-remove-top uk-padding-remove-bottom">Meta</div></div></a>
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
        </li><!-- Metadata Button :: END -->
        <li class="uk-link-toggle uk-button uk-button-default uk-button-small uk-width-1-1 uk-border-rounded uk-margin-small"><!-- View Asciidoc Source Button :: START -->
            <a class="uk-link-heading" href="#modal-full-source" uk-toggle><div class="uk-grid-medium uk-flex-middle" uk-grid><div class="uk-width-auto uk-padding-remove-top uk-padding-remove-bottom"><span class="uk-link-heading" uk-icon="icon: code; ratio: 1.0;"></span></div><div class="uk-width-auto uk-padding-small uk-padding-remove-top uk-padding-remove-bottom">Source</div></div></a>
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
        </li><!-- View Source Button :: END -->
        <!-- Delete Button :: START -->
        <!--
        <li class="uk-link-toggle uk-button uk-button-danger uk-button-small uk-width-1-1 uk-border-rounded">
            <a class="uk-link-heading" href="#"><div class="uk-grid-medium uk-flex-middle" uk-grid><div class="uk-width-auto uk-padding-remove-top uk-padding-remove-bottom"><span class="uk-link-heading uk-text-danger" uk-icon="icon: trash; ratio: 1.0;" class="uk-text-danger"></span></div><div class="uk-width-auto uk-padding-small uk-padding-remove-top uk-padding-remove-bottom"><span class="uk-text-danger">Delete</span></div></div></a>
        </li>
        -->
        <!-- Delete Button :: END -->
% endif
<!-- Template SECTION_ACTIONS.tpl :: END -->


