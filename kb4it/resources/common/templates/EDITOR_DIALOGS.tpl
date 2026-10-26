<!-- EDITOR DATA :: START -->
<link rel="stylesheet" href="resources/editor/kb4it-editor.css">
<script id="kb-add-keys" type="application/json">${var['page']['keys_json'] | n}</script>
<script id="kb-add-skeletons" type="application/json">${var['page']['skeletons_json'] | n}</script>
<!-- EDITOR DATA :: END -->

% for cat in var['page']['categories']:
<!-- EDITOR DIALOG :: START -->
<!-- Full-screen dialog to write a new document of one category (see its id). -->
<dialog id="modal-add-${cat['id']}" class="kb-dialog-modal">
    <div class="kb-dialog">

        <!-- DIALOG HEADER :: START -->
        <div class="kb-dialog-header" tabindex="-1" style="border-bottom: 3px solid ${cat['color']};">
            <span class="kb-dialog-title" style="color: ${cat['color']};">Add ${cat['name']}</span>
            <span class="kb-dialog-desc">${cat['description']}</span>
            <div class="kb-dialog-actions">
                <button id="kb-save-${cat['id']}" class="kb-btn kb-btn-primary kb-btn-small" type="button"
                        data-kb-save="${cat['id']}"><svg class="kb-btn-icon" width="17" height="17" viewBox="0 0 20 20" fill="none" stroke="currentColor" aria-hidden="true"><polyline points="14,10 9.5,14.5 5,10"/><rect width="13" height="1" x="3" y="17" fill="currentColor" stroke="none"/><line x1="9.5" y1="13.91" x2="9.5" y2="3"/></svg><span class="kb-save-label">Save</span></button>
                <button class="kb-btn kb-btn-small" type="button"
                        data-kb-copy="${cat['id']}"><svg class="kb-btn-icon" width="17" height="17" viewBox="0 0 20 20" fill="none" stroke="currentColor" aria-hidden="true"><rect width="12" height="16" x="3.5" y="2.5"/><polyline points="5 0.5 17.5 0.5 17.5 17"/></svg>Copy</button>
                <button class="kb-btn kb-btn-small" type="button"
                        data-kb-close="${cat['id']}">Close</button>
            </div>
        </div>
        <!-- DIALOG HEADER :: END -->

        <!-- DIALOG BODY :: START -->
        <div class="kb-dialog-body">

            <!-- TEMPLATE EDITOR :: START -->
            <div class="kb-pane-left">
                <div class="kb-pane-label">Template</div>
                <div id="kb-toolbar-${cat['id']}" class="kb-toolbar"></div>
                <div id="kb-editor-${cat['id']}" class="kb-editor-host"></div>
            </div>
            <!-- TEMPLATE EDITOR :: END -->

            <!-- PROPERTIES PANE :: START -->
            <div class="kb-pane-right">
                <div class="kb-pane-label">Properties</div>
                <div class="kb-props-wrap">
                    <div id="kb-props-${cat['id']}"></div>
                </div>
            </div>
            <!-- PROPERTIES PANE :: END -->

        </div>
        <!-- DIALOG BODY :: END -->

    </div>
</dialog>
<!-- EDITOR DIALOG :: END -->
% endfor

<!-- EDITOR SCRIPTS :: START -->
<script src="resources/editor/codemirror.min.js"></script>
<script src="resources/editor/kb4it-frontmatter.js"></script>
<script src="resources/editor/kb4it-editor.js"></script>
<!-- EDITOR SCRIPTS :: END -->
