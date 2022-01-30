<!-- Template SECTION_ACTIONS.tpl :: START -->
% if var['has_toc']:
<div class="uk-flex uk-flex-center">
    <div class="uk-card uk-card-body"><button class="uk-button uk-button-primary uk-border-rounded"><span uk-icon="icon: pencil"></span><span class="uk-text-bold"> Edit</span></button></div>
    <div class="uk-card uk-card-body"><button class="uk-button uk-button-primary uk-border-rounded" onclick="window.print()"><span uk-icon="icon: print"></span><span class="uk-text-bold"> Print</span></button></div>
    <div class="uk-card uk-card-body">
        <!-- View Asciidoc Source Button :: START -->
        <a class="uk-button uk-button-primary uk-border-rounded" href="#modal-full-source" uk-toggle><span uk-icon="icon: code"></span><span class="uk-text-bold"> Source</span></a>
        <div id="modal-full-source" class="uk-modal-full" uk-modal>
            <div class="uk-modal-dialog">
                <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                    <div class="uk-padding-large uk-background-muted">
                        <div class="uk-text-lead uk-text-center uk-text-danger">Source</div>
                        <div class="uk-text-lead">${var['basename_adoc']}&nbsp;<a onclick="copyToClipboard()" class="uk-icon-link uk-margin-small-right" uk-icon="copy"></a></div>
                        <textarea id="source-code" class="uk-width-1-1 uk-height-viewport">${var['source_adoc']}</textarea>
                    </div>
                </div>
            </div>
        </div> 
        <!-- View Source Button :: END -->
    </div>    
    <div class="uk-card uk-card-body"></div>
    <div class="uk-card uk-card-body"><button class="uk-button uk-button-danger uk-border-rounded"><span uk-icon="icon: trash"></span><span class="uk-text-bold"> Delete</span></button></div>
</div>
% endif
<!-- Template SECTION_ACTIONS.tpl :: END -->


