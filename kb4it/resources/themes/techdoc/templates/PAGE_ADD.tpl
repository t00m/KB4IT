= Add document

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

<%!
CATEGORIES = [
    {
        'id':    'change',
        'name':  'Change',
        'icon':  'cog',
        'color': '#f0506e',
        'desc':  'A planned or completed modification to a system, process, or infrastructure component.',
    },
    {
        'id':    'incident',
        'name':  'Incident',
        'icon':  'warning',
        'color': '#faa05a',
        'desc':  'An unexpected disruption or quality degradation of a service.',
    },
    {
        'id':    'meeting',
        'name':  'Meeting',
        'icon':  'users',
        'color': '#32d296',
        'desc':  'Minutes or agenda for a team meeting, review, or discussion.',
    },
    {
        'id':    'note',
        'name':  'Note',
        'icon':  'file-text',
        'color': '#1e87f0',
        'desc':  'A free-form note, observation, or brief record.',
    },
    {
        'id':    'post',
        'name':  'Post',
        'icon':  'comment',
        'color': '#1e87f0',
        'desc':  'A blog-style post, announcement, or article.',
    },
    {
        'id':    'procedure',
        'name':  'Procedure',
        'icon':  'list',
        'color': '#32d296',
        'desc':  'A step-by-step operational procedure or runbook.',
    },
    {
        'id':    'report',
        'name':  'Report',
        'icon':  'album',
        'color': '#888888',
        'desc':  'A formal or informal report summarising findings, metrics, or status.',
    },
    {
        'id':    'task',
        'name':  'Task',
        'icon':  'check',
        'color': '#faa05a',
        'desc':  'A work item or action to be tracked and completed.',
    },
]
%>

++++
<div class="uk-container kb-add">

    <div class="kb-add-note uk-alert-primary" uk-alert>
        <span uk-icon="icon: info; ratio: 0.9"></span>
        <strong>Note:</strong> KB4IT is a static site generator — it cannot create files for you.
        Click <em>Create</em> on any card to see the AsciiDoc skeleton for that document type,
        copy it, and save it as a <code>.adoc</code> file in your repository's
        <strong>source</strong> directory (or commit it directly to your Git repository).
        Rebuild the site afterwards to make the new document appear.
    </div>

    <div class="uk-grid-small uk-child-width-1-2@s uk-child-width-1-4@m" uk-grid>
% for cat in CATEGORIES:
        <div>
            <div class="uk-card uk-card-default uk-card-hover uk-card-small kb-add-card" style="border-top: 3px solid ${cat['color']};">
                <div class="uk-card-header kb-add-card-header">
                    <h3 class="uk-card-title uk-margin-remove kb-add-card-title">
                        <span uk-icon="icon: ${cat['icon']}; ratio: 0.95" style="color: ${cat['color']};"></span>
                        Add ${cat['name']}
                    </h3>
                </div>
                <div class="uk-card-body kb-add-card-body">
                    <p class="uk-margin-remove">${cat['desc']}</p>
                </div>
                <div class="uk-card-footer kb-add-card-footer">
                    <a href="#modal-add-${cat['id']}" class="uk-button uk-button-small uk-button-primary" uk-toggle>Create</a>
                </div>
            </div>
        </div>
% endfor
    </div>

</div>

<!-- Skeleton modals — one per category -->
% for cat in CATEGORIES:
<div id="modal-add-${cat['id']}" class="uk-modal-full" uk-modal>
    <div class="uk-modal-dialog uk-height-viewport">
        <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
        <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
            <div class="uk-padding-large uk-background-muted">
                <div class="uk-text-lead uk-text-center uk-margin-small-bottom" style="color: ${cat['color']};">${cat['name']} skeleton</div>
                <div class="uk-text-lead uk-margin-small-bottom">
                    new_${cat['id']}.adoc
                    &nbsp;<a onclick="copySkeletonToClipboard('skeleton-${cat['id']}')" class="uk-icon-link uk-margin-small-right uk-link-toggle" uk-icon="icon: copy; ratio: 1.0" uk-tooltip="title: Copy to clipboard"></a>
                </div>
                <textarea id="skeleton-${cat['id']}" class="uk-width-1-1 uk-height-viewport">${var['page']['skeletons'][cat['id']]}</textarea>
            </div>
        </div>
    </div>
</div>
% endfor

<script>
function copySkeletonToClipboard(id) {
    var el = document.getElementById(id);
    el.select();
    el.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(el.value).catch(function() {
        document.execCommand("copy");
    });
    UIkit.notification({message: 'Skeleton copied to clipboard', status: 'success', timeout: 2000});
}
</script>
++++
