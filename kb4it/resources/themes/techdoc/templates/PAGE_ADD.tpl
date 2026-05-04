= Add document

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

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

++++
<script id="kb-add-keys" type="application/json">${var['page']['keys_json']}</script>
<script id="kb-add-skeletons" type="application/json">${var['page']['skeletons_json']}</script>

<div class="uk-container kb-add">

    <div class="kb-add-note uk-alert-primary" uk-alert>
        <span uk-icon="icon: info; ratio: 0.9"></span>
        <strong>Note:</strong> KB4IT is a static site generator — it cannot create files for you.
        Click <em>Create</em> on any card, edit the template, then copy the
        ready-to-use AsciiDoc file into your repository's <strong>source</strong>
        directory and rebuild.
    </div>

% if var['repo']['git'] == True:
    <div class="kb-add-note uk-alert-primary" uk-alert>
        <span uk-icon="icon: git-branch; ratio: 0.9"></span>
        <strong>Online repository:</strong> The document source is hosted at
        <a href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}" target="_blank">
            ${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}
        </a> — navigate to the source folder to upload your new file.
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
                            onclick="kbAddOpen('${cat['id']}')">Create</button>
                </div>
            </div>
        </div>
% endfor
    </div>

</div><!-- /kb-add -->

<!-- ── Full-screen modal — one per category ── -->
% for cat in CATEGORIES:
<div id="modal-add-${cat['id']}" class="uk-modal-full" uk-modal>
    <div class="kb-dialog">

        <!-- Header -->
        <div class="kb-dialog-header" style="border-bottom: 3px solid ${cat['color']};">
            <span uk-icon="icon: ${cat['icon']}; ratio: 1.2"
                  style="color: ${cat['color']}; flex-shrink: 0;"></span>
            <span class="kb-dialog-title" style="color: ${cat['color']};">Add ${cat['name']}</span>
            <span class="kb-dialog-desc">${cat['desc']}</span>
            <div class="kb-dialog-actions">
                <button class="uk-button uk-button-primary uk-button-small"
                        onclick="kbAddCopy('${cat['id']}')">
                    <span uk-icon="icon: copy; ratio: 0.85"></span> Copy
                </button>
                <button class="uk-button uk-button-small uk-modal-close uk-close" type="button" uk-close> Close </button>
            </div>
        </div>

        <!-- Split body -->
        <div class="kb-dialog-body">

            <!-- Left: editable AsciiDoc template -->
            <div class="kb-pane-left">
                <div class="kb-pane-label">Template</div>
                <textarea id="kb-editor-${cat['id']}"
                          class="kb-editor"
                          spellcheck="false"></textarea>
            </div>

            <!-- Right: key values reference as accordion word clouds -->
            <div class="kb-pane-right">
                <div class="kb-pane-label">Values reference</div>
                <div class="kb-accord-wrap">
                    <div id="kb-accord-${cat['id']}"></div>
                </div>
            </div>

        </div><!-- /kb-dialog-body -->

    </div><!-- /kb-dialog -->
</div><!-- /modal -->
% endfor

<style>
/* ── Dialog chrome ── */
.kb-dialog {
    position: relative;
    overflow: hidden;
    height: 100vh;
    display: flex;
    flex-direction: column;
}
.kb-dialog-header {
    flex-shrink: 0;
    padding: 11px 20px;
    background: #fff;
    display: flex;
    align-items: center;
    gap: 10px;
}
.kb-dialog-title {
    font-size: 1rem;
    font-weight: 700;
    flex-shrink: 0;
}
.kb-dialog-desc {
    flex: 1;
    min-width: 0;
    font-size: 0.82rem;
    color: #888;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.kb-dialog-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    margin-left: auto;
}

/* ── Split body ── */
.kb-dialog-body {
    flex: 1;
    display: flex;
    overflow: hidden;
}

/* ── Left pane: editor ── */
.kb-pane-left {
    flex: 3;
    display: flex;
    flex-direction: column;
    min-width: 0;
    border-right: 1px solid #ddd;
}

/* ── Right pane: accordion ── */
.kb-pane-right {
    flex: 2;
    display: flex;
    flex-direction: column;
    min-width: 0;
    background: #fff;
}
.kb-accord-wrap {
    flex: 1;
    overflow-y: auto;
    padding: 8px 16px 16px;
}

/* ── Panel label strip ── */
.kb-pane-label {
    flex-shrink: 0;
    padding: 5px 16px;
    font-size: 0.69rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #bbb;
    background: #f8f8f8;
    border-bottom: 1px solid #ebebeb;
}

/* ── Editor textarea ── */
.kb-editor {
    flex: 1;
    resize: none;
    border: none;
    outline: none;
    padding: 20px 24px;
    font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
    font-size: 0.84rem;
    line-height: 1.65;
    background: #1e1e1e;
    color: #d4d4d4;
}

/* ── Accordion tuning for right pane ── */
.kb-accord-wrap .uk-accordion { margin: 0; }
.kb-accord-wrap .uk-accordion > li { border-bottom: 1px solid #f0f0f0; }
.kb-accord-wrap .uk-accordion-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #555;
    padding: 7px 0 6px;
    line-height: 1.3;
}
.kb-accord-wrap .uk-accordion-content { padding-top: 2px; padding-bottom: 8px; }

/* ── Word cloud (no links) ── */
.kb-wcloud {
    display: flex;
    flex-wrap: wrap;
    gap: 3px 7px;
    padding: 2px 0 2px;
}
.kb-wcloud-word {
    --kb-weight: 0;
    display: inline-block;
    cursor: default;
    font-size: calc(0.72rem + var(--kb-weight) * 1.0rem);
    font-weight: calc(400 + var(--kb-weight) * 300);
    color: hsl(210, 14%, calc(60% - var(--kb-weight) * 36%));
    line-height: 1.6;
}
</style>

<script>
(function () {
    var KB_KEYS = JSON.parse(document.getElementById('kb-add-keys').textContent);
    var KB_SKEL = JSON.parse(document.getElementById('kb-add-skeletons').textContent);

    /* YYYY-MM-DD HH:MM:00 in local time */
    function timestamp() {
        var d = new Date();
        var p = function (n) { return String(n).padStart(2, '0'); };
        return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
               ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':00';
    }

    /* Extract ordered key names and default values from the skeleton header */
    function parseKeys(catId) {
        var keys = [];
        var lines = KB_SKEL[catId].split('\n');
        for (var i = 0; i < lines.length; i++) {
            if (lines[i].indexOf('// END-OF-HEADER') === 0) break;
            var m = lines[i].match(/^:([^:]+):\s*(.*)/);
            if (m) keys.push({ name: m[1], val: m[2].trim() });
        }
        return keys;
    }

    /* Build the clean editable template for the left pane */
    function buildTemplate(catId) {
        var keys = parseKeys(catId);
        var out = ['= ', ''];
        keys.forEach(function (key) {
            var val = key.name === 'Date' ? timestamp() : key.val;
            out.push(':' + key.name + ':' + (val ? ' ' + val : ''));
        });
        out.push('');
        out.push('// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE');

        /* Append body sections from the skeleton (everything after EOHMARK) */
        var skelLines = KB_SKEL[catId].split('\n');
        var inBody = false;
        for (var i = 0; i < skelLines.length; i++) {
            if (skelLines[i].indexOf('// END-OF-HEADER') === 0) { inBody = true; continue; }
            if (inBody) out.push(skelLines[i]);
        }
        return out.join('\n');
    }

    /* Build the accordion + word clouds for the right pane */
    function buildAccordion(catId) {
        var container = document.getElementById('kb-accord-' + catId);
        container.innerHTML = '';

        var ul = document.createElement('ul');
        ul.setAttribute('uk-accordion', '');

        Object.keys(KB_KEYS).sort(function (a, b) {
            return a.toLowerCase().localeCompare(b.toLowerCase());
        }).forEach(function (keyName) {
            var items = KB_KEYS[keyName];

            var li = document.createElement('li');

            var a = document.createElement('a');
            a.className = 'uk-accordion-title';
            a.href = '';
            a.innerHTML = keyName +
                (items.length > 0
                    ? '<span style="font-size:0.7rem;font-weight:400;color:#ccc;margin-left:5px;">(' + items.length + ')</span>'
                    : '');

            var div = document.createElement('div');
            div.className = 'uk-accordion-content';

            var cloud = document.createElement('div');
            cloud.className = 'kb-wcloud';

            if (items.length > 0) {
                var maxC = 1;
                items.forEach(function (it) { if (it.c > maxC) maxC = it.c; });
                var logMax = Math.log(1 + maxC) || 1;
                items.forEach(function (it) {
                    var w = Math.log(1 + it.c) / logMax;
                    var sp = document.createElement('span');
                    sp.className = 'kb-wcloud-word';
                    sp.style.setProperty('--kb-weight', w.toFixed(3));
                    sp.textContent = it.v;
                    sp.title = it.c + (it.c === 1 ? ' document' : ' documents');
                    cloud.appendChild(sp);
                });
            } else {
                var empty = document.createElement('span');
                empty.style.cssText = 'font-size:0.75rem;color:#bbb;font-style:italic;';
                empty.textContent = 'No values yet';
                cloud.appendChild(empty);
            }

            div.appendChild(cloud);
            li.appendChild(a);
            li.appendChild(div);
            ul.appendChild(li);
        });

        container.appendChild(ul);
    }

    window.kbAddOpen = function (catId) {
        document.getElementById('kb-editor-' + catId).value = buildTemplate(catId);
        buildAccordion(catId);
        UIkit.modal('#modal-add-' + catId).show();
    };

    window.kbAddCopy = function (catId) {
        var el = document.getElementById('kb-editor-' + catId);
        navigator.clipboard.writeText(el.value).catch(function () {
            el.select();
            document.execCommand('copy');
        });
        UIkit.notification({ message: 'Copied to clipboard', status: 'success', timeout: 2000 });
    };
})();
</script>
++++
