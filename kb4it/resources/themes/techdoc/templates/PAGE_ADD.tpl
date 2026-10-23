<%!
CATEGORIES = [
    {'id': 'change',    'name': 'Change',    'icon': 'cog',       'color': '#f0506e', 'desc': 'A planned or completed modification to a system, process, or infrastructure component.'},
    {'id': 'incident',  'name': 'Incident',  'icon': 'warning',   'color': '#faa05a', 'desc': 'An unexpected disruption or quality degradation of a service.'},
    {'id': 'meeting',   'name': 'Meeting',   'icon': 'users',     'color': '#32d296', 'desc': 'Minutes or agenda for a team meeting, review, or discussion.'},
    {'id': 'note',      'name': 'Note',      'icon': 'file-text', 'color': '#1e87f0', 'desc': 'A free-form note, observation, or brief record.'},
    {'id': 'post',      'name': 'Post',      'icon': 'comment',   'color': '#1e87f0', 'desc': 'A blog-style post, announcement, or article.'},
    {'id': 'procedure', 'name': 'Procedure', 'icon': 'list',      'color': '#32d296', 'desc': 'A step-by-step operational procedure or runbook.'},
    {'id': 'report',    'name': 'Report',    'icon': 'album',     'color': '#888888', 'desc': 'A formal or informal report summarising findings, metrics, or status.'},
    {'id': 'task',      'name': 'Task',      'icon': 'check',     'color': '#faa05a', 'desc': 'A work item or action to be tracked and completed.'},
]
%>

<link rel="stylesheet" href="resources/editor/kb4it-editor.css">
<script id="kb-add-keys" type="application/json">${var['page']['keys_json'] | n}</script>
<script id="kb-add-skeletons" type="application/json">${var['page']['skeletons_json'] | n}</script>

<div class="uk-container kb-add">

    <div class="kb-add-note uk-alert-primary" uk-alert>
        <span uk-icon="icon: info; ratio: 0.9"></span>
        <strong>Note:</strong> This page saves or downloads the Markdown file for you.
        Click <em>Create</em> on any card, edit the template, then <em>Save</em> it
        (or <em>Copy</em> the text). Put the file in your repository's <strong>source</strong>
        folder and rebuild.
    </div>

% if var.get('git_ok'):
    <div class="kb-add-note uk-alert-primary" uk-alert>
        <span uk-icon="icon: git-branch; ratio: 0.9"></span>
        <strong>Online repository:</strong> The document source is hosted at
        <a href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}" target="_blank">
            ${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}
        </a>,  navigate to the source folder to upload your new file.
    </div>
% endif

    <div class="uk-grid-small uk-child-width-1-2@s uk-child-width-1-4@m" uk-grid>
% for cat in CATEGORIES:
        <div>
            <div class="uk-card uk-card-default uk-card-hover uk-card-small kb-add-card"
                 style="border-top: 3px solid ${cat['color']};">
                <div class="uk-card-header kb-add-card-header">
                    <h3 class="uk-card-title uk-margin-remove kb-add-card-title">
                        <span uk-icon="icon: ${cat['icon']}; ratio: 0.95"
                              style="color: ${cat['color']};"></span>
                        Add ${cat['name']}
                    </h3>
                </div>
                <div class="uk-card-body kb-add-card-body">
                    <p class="uk-margin-remove">${cat['desc']}</p>
                </div>
                <div class="uk-card-footer kb-add-card-footer">
                    <button class="uk-button uk-button-small uk-button-primary"
                            data-kb-open="${cat['id']}">Create</button>
                </div>
            </div>
        </div>
% endfor
    </div>

</div><!-- /kb-add -->

<!-- ── Full-screen modal,  one per category ── -->
% for cat in CATEGORIES:
<dialog id="modal-add-${cat['id']}" class="kb-dialog-modal">
    <div class="kb-dialog">

        <!-- Header -->
        <div class="kb-dialog-header" tabindex="-1" style="border-bottom: 3px solid ${cat['color']};">
            <span class="kb-dialog-title" style="color: ${cat['color']};">Add ${cat['name']}</span>
            <span class="kb-dialog-desc">${cat['desc']}</span>
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
