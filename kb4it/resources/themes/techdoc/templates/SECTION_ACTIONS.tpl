<!-- Template SECTION_ACTIONS.tpl :: START -->
% if var['has_toc']:
<div class="uk-flex uk-flex-center">
    <div class="uk-card-small uk-card-body"><a href="https://${var['theme']['git_server']}/${var['theme']['git_user']}/${var['theme']['git_repo']}/edit/${var['theme']['git_branch']}/${var['theme']['git_path']}/${var['basename_adoc']}" target="_blank"><span uk-icon="icon: pencil; ratio: 1.5;"></span></span></a></div>
    <div class="uk-card-small uk-card-body">
        <!-- Metadata Button :: START -->
        <a class="" href="#modal-metadata" uk-toggle><span uk-icon="icon: hashtag; ratio: 1.5;"></span></a>
        <div id="modal-metadata" class="uk-modal-full" uk-modal>
            <div class="uk-modal-dialog">
                <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                    <div class="uk-padding-large uk-background-muted">
                        <div class="uk-text-lead uk-text-center uk-text-primary">Metadata</div>
                        <div class="">${var['metadata']}</div>                        
                    </div>
                </div>
            </div>
        </div> 
        <!-- Metadata Button :: END -->
    </div>    
    <div class="uk-card-small uk-card-body"><a onclick="window.print()"><span uk-icon="icon: print; ratio: 1.5;"></span></a></div>
    <div class="uk-card-small uk-card-body">
        <!-- View Asciidoc Source Button :: START -->
        <a class="" href="#modal-full-source" uk-toggle><span uk-icon="icon: code; ratio: 1.5;"></span></a>
        <div id="modal-full-source" class="uk-modal-full" uk-modal>
            <div class="uk-modal-dialog">
                <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                    <div class="uk-padding-large uk-background-muted">
                        <div class="uk-text-lead uk-text-center uk-text-danger">Source</div>
                        <div class="uk-text-lead">${var['basename_adoc']}&nbsp;<a onclick="copyToClipboard()" class="uk-icon-link uk-margin-small-right" uk-icon="copy; ratio: 1.5;" uk-tooltip="title: Copy to clipboard"></a></div>
                        <textarea id="source-code" class="uk-width-1-1 uk-height-viewport">${var['source_adoc']}</textarea>
                    </div>
                </div>
            </div>
        </div> 
        <!-- View Source Button :: END -->
    </div>    
    <div class="uk-card-small uk-card-body"></div>
    <div class="uk-card-small uk-card-body"><a href="#" class=""><span uk-icon="icon: trash; ratio: 1.5;" class="uk-text-danger"></span></a></div>
</div>
% endif
<!-- Template SECTION_ACTIONS.tpl :: END -->


