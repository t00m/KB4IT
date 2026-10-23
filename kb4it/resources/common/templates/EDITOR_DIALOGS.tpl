<link rel="stylesheet" href="resources/editor/kb4it-editor.css">
<script id="kb-add-keys" type="application/json">${var['page']['keys_json'] | n}</script>
<script id="kb-add-skeletons" type="application/json">${var['page']['skeletons_json'] | n}</script>

<!-- Full-screen modal, one per category -->
% for cat in var['page']['categories']:
<dialog id="modal-add-${cat['id']}" class="kb-dialog-modal">
    <div class="kb-dialog">

        <!-- Header -->
        <div class="kb-dialog-header" tabindex="-1" style="border-bottom: 3px solid ${cat['color']};">
            <span class="kb-dialog-title" style="color: ${cat['color']};">Add ${cat['name']}</span>
            <span class="kb-dialog-desc">${cat['description']}</span>
            <div class="kb-dialog-actions">
                <button id="kb-save-${cat['id']}" class="kb-btn kb-btn-primary kb-btn-small" type="button"
                        data-kb-save="${cat['id']}"><span class="kb-save-label">Save</span></button>
                <button class="kb-btn kb-btn-small" type="button"
                        data-kb-copy="${cat['id']}">Copy</button>
                <button class="kb-btn kb-btn-small" type="button"
                        data-kb-close="${cat['id']}">Close</button>
            </div>
        </div>

        <!-- Split body -->
        <div class="kb-dialog-body">

            <!-- Left: editable Markdown template -->
            <div class="kb-pane-left">
                <div class="kb-pane-label">Template</div>
                <div id="kb-toolbar-${cat['id']}" class="kb-toolbar"></div>
                <div id="kb-editor-${cat['id']}" class="kb-editor-host"></div>
            </div>

            <!-- Right: visual frontmatter editor -->
            <div class="kb-pane-right">
                <div class="kb-pane-label">Properties</div>
                <div class="kb-props-wrap">
                    <div id="kb-props-${cat['id']}"></div>
                </div>
            </div>

        </div><!-- /kb-dialog-body -->

    </div><!-- /kb-dialog -->
</dialog><!-- /modal -->
% endfor

<script src="resources/editor/codemirror.min.js"></script>
<script src="resources/editor/kb4it-frontmatter.js"></script>
<script src="resources/editor/kb4it-editor.js"></script>
