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
<!-- Baked-in data for the JS form builder -->
<script id="kb-add-keys" type="application/json">${var['page']['keys_json']}</script>
<script id="kb-add-skeletons" type="application/json">${var['page']['skeletons_json']}</script>

<div class="uk-container kb-add">

    <div class="kb-add-note uk-alert-primary" uk-alert>
        <span uk-icon="icon: info; ratio: 0.9"></span>
        <strong>Note:</strong> KB4IT is a static site generator — it cannot create files for you.
        Click <em>Create</em> on any card, fill in the metadata form, then copy the
        ready-to-use AsciiDoc file into your repository's <strong>source</strong>
        directory and rebuild.
    </div>

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
                            onclick="kb_add_open('${cat['id']}')">Create</button>
                </div>
            </div>
        </div>
% endfor
    </div>

</div><!-- /kb-add -->

<!-- ── Modal dialogs — one per category ── -->
% for cat in CATEGORIES:
<div id="modal-add-${cat['id']}" class="uk-modal-full" uk-modal>
    <div class="uk-modal-dialog" style="position:relative; overflow:hidden; height:100vh;">

        <!-- ── STEP 1: metadata form ── -->
        <div id="add-form-${cat['id']}"
             style="position:absolute; inset:0; display:flex; flex-direction:column;">

            <!-- Header -->
            <div style="flex-shrink:0; padding:14px 24px 12px;
                        border-bottom:3px solid ${cat['color']};
                        background:#fff; display:flex; align-items:center; gap:12px;">
                <span uk-icon="icon: ${cat['icon']}; ratio:1.3"
                      style="color:${cat['color']};"></span>
                <div style="flex:1; min-width:0;">
                    <div style="font-size:1.05rem; font-weight:700; color:${cat['color']};">
                        Add ${cat['name']}
                    </div>
                    <div class="uk-text-muted uk-text-small">${cat['desc']}</div>
                </div>
                <button class="uk-modal-close-full uk-close-large" type="button" uk-close
                        style="flex-shrink:0;"></button>
            </div>

            <!-- Body: form -->
            <div style="flex:1; overflow:auto; padding:24px;">
                <div style="max-width:680px; margin:0 auto;">
                    <form id="form-${cat['id']}" class="uk-form-stacked"></form>
                </div>
            </div>

            <!-- Footer -->
            <div style="flex-shrink:0; padding:12px 24px; border-top:1px solid #e8e8e8;
                        background:#fafafa; display:flex; justify-content:flex-end; gap:8px;">
                <button class="uk-button uk-button-default uk-modal-close"
                        type="button">Cancel</button>
                <button class="uk-button uk-button-primary"
                        onclick="kb_add_generate('${cat['id']}')">
                    <span uk-icon="icon: arrow-right; ratio:0.9"></span> Create
                </button>
            </div>
        </div><!-- /add-form -->

        <!-- ── STEP 2: filled skeleton preview ── -->
        <div id="add-preview-${cat['id']}" class="uk-hidden"
             style="position:absolute; inset:0; display:flex; flex-direction:column;">

            <!-- Header -->
            <div style="flex-shrink:0; padding:10px 20px;
                        border-bottom:3px solid ${cat['color']};
                        background:#fff; display:flex; align-items:center;
                        gap:10px; flex-wrap:wrap;">
                <button class="uk-button uk-button-default uk-button-small"
                        onclick="kb_add_back('${cat['id']}')">
                    <span uk-icon="icon: arrow-left; ratio:0.85"></span> Back
                </button>
                <span style="font-weight:600; color:${cat['color']};">${cat['name']} skeleton</span>
                <code id="add-filename-${cat['id']}"
                      class="uk-text-small uk-text-muted"></code>
                <div style="margin-left:auto; display:flex; gap:8px;">
                    <button class="uk-button uk-button-primary uk-button-small"
                            onclick="kb_add_copy('${cat['id']}')">
                        <span uk-icon="icon: copy; ratio:0.85"></span> Copy
                    </button>
                    <button class="uk-modal-close uk-button uk-button-default uk-button-small"
                            type="button">Close</button>
                </div>
            </div>

            <!-- Body: textarea fills remaining height -->
            <textarea id="add-skeleton-${cat['id']}"
                      style="flex:1; resize:none; border:none; outline:none; padding:16px 24px;
                             font-family:'SF Mono','Fira Code',Consolas,monospace;
                             font-size:0.83rem; line-height:1.55; background:#1e1e1e;
                             color:#d4d4d4;"
                      spellcheck="false"></textarea>
        </div><!-- /add-preview -->

    </div><!-- /uk-modal-dialog -->
</div><!-- /modal -->
% endfor

<!-- ── Shared value picker (plain overlay — avoids UIKit modal stacking issues) ── -->
<div id="kb-add-picker"
     style="display:none; position:fixed; inset:0; z-index:1050;
            align-items:center; justify-content:center;
            background:rgba(0,0,0,0.45);">
    <div style="background:#fff; border-radius:6px; padding:20px 24px;
                width:500px; max-width:calc(100vw - 32px);
                max-height:calc(100vh - 80px); display:flex; flex-direction:column;
                box-shadow:0 14px 30px rgba(0,0,0,0.18);"
         onclick="event.stopPropagation()">
        <div style="display:flex; align-items:center; justify-content:space-between;
                    margin-bottom:12px; flex-shrink:0;">
            <h3 id="kb-picker-title"
                style="margin:0; font-size:1rem; font-weight:700;"></h3>
            <button onclick="kb_picker_cancel()"
                    style="background:none; border:none; cursor:pointer;
                           font-size:1.4rem; line-height:1; color:#999; padding:0;"
                    title="Cancel">&times;</button>
        </div>
        <input id="kb-picker-filter" type="text" class="uk-input uk-form-small"
               placeholder="Filter…" oninput="kb_picker_filter()" style="flex-shrink:0;">
        <div id="kb-picker-chips" class="kb-tag-list"
             style="flex:1; overflow-y:auto; padding:6px 0; margin-top:10px; min-height:60px;"></div>
        <input id="kb-picker-custom" type="text" class="uk-input uk-form-small"
               style="margin-top:8px; flex-shrink:0;"
               placeholder="Custom value — press Enter to add">
        <div style="display:flex; justify-content:space-between; align-items:center;
                    margin-top:14px; flex-shrink:0;">
            <button class="uk-button uk-button-link uk-text-small"
                    style="color:#aaa; padding:0;"
                    onclick="kb_picker_clear()">Clear all</button>
            <button class="uk-button uk-button-primary uk-button-small"
                    onclick="kb_picker_done()">
                <span uk-icon="icon: check; ratio:0.85"></span> Done
            </button>
        </div>
    </div>
</div>

<style>
.kb-tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 5px;
    padding: 4px 0 2px;
    min-height: 30px;
}
.kb-tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 3px;
    font-size: 0.78rem;
    cursor: pointer;
    background: #f0f2f5;
    color: #555;
    border: 1px solid #dde1e7;
    user-select: none;
    line-height: 1.45;
    transition: background 0.1s, color 0.1s, border-color 0.1s;
}
.kb-tag:hover {
    background: #dbeafe;
    border-color: #93c5fd;
    color: #1e40af;
}
.kb-tag.kb-tag-selected {
    background: #1e87f0;
    color: #fff;
    border-color: #1e87f0;
}
.kb-tag.kb-tag-selected:hover {
    background: #1670d0;
    border-color: #1670d0;
}
.kb-tag-custom-input {
    margin-top: 6px;
    font-size: 0.82rem;
}
.kb-picker-trigger {
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    user-select: none;
    height: auto;
    min-height: 30px;
    padding: 4px 10px;
    gap: 6px;
}
.kb-picker-trigger:hover { border-color: #1e87f0; }
.kb-trigger-summary {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.82rem;
}
</style>

<script>
(function () {
    var KB_KEYS = JSON.parse(document.getElementById('kb-add-keys').textContent);
    var KB_SKEL = JSON.parse(document.getElementById('kb-add-skeletons').textContent);

    /* ── small helpers ── */
    function today() { return new Date().toISOString().slice(0, 10); }

    function slugify(s) {
        return (s || 'document')
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '_')
            .replace(/^_+|_+$/g, '') || 'document';
    }

    /* Parse `:Key: DefaultValue` lines from the skeleton header */
    function parseAttrs(catId) {
        var attrs = [];
        var lines = KB_SKEL[catId].split('\n');
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            if (line.indexOf('// END-OF-HEADER') === 0) break;
            if (line.indexOf('//') === 0 || line.trim() === '') continue;
            if (i === 0 && /^=\s+/.test(line)) continue;
            var m = line.match(/^:([^:]+):\s*(.*)/);
            if (m) attrs.push({ key: m[1], def: m[2].trim() });
        }
        return attrs;
    }

    /* Build one form row */
    function makeRow(catId, key, label, defVal, fixed) {
        var wrap = document.createElement('div');
        wrap.className = 'uk-margin-small';

        var lbl = document.createElement('label');
        lbl.className = 'uk-form-label';
        lbl.setAttribute('for', 'add-f-' + catId + '-' + key);
        lbl.textContent = label;
        if (fixed) {
            var badge = document.createElement('span');
            badge.textContent = 'fixed';
            badge.style.cssText = 'font-size:0.55rem; font-weight:600; text-transform:uppercase; ' +
                'background:#e8e8e8; color:#999; border-radius:2px; padding:1px 4px; ' +
                'margin-left:6px; vertical-align:middle;';
            lbl.appendChild(badge);
        }

        var ctrl = document.createElement('div');
        ctrl.className = 'uk-form-controls';

        if (key === 'Date') {
            /* Date picker */
            var inp = document.createElement('input');
            inp.type = 'date'; inp.id = 'add-f-' + catId + '-' + key;
            inp.name = key; inp.className = 'uk-input uk-form-small';
            inp.value = today();
            ctrl.appendChild(inp);

        } else if (fixed) {
            /* Read-only fixed value */
            var inp = document.createElement('input');
            inp.type = 'text'; inp.id = 'add-f-' + catId + '-' + key;
            inp.name = key; inp.className = 'uk-input uk-form-small';
            inp.value = defVal; inp.readOnly = true;
            inp.style.cssText = 'background:#f5f5f5; color:#aaa; cursor:not-allowed;';
            ctrl.appendChild(inp);

        } else {
            var known = KB_KEYS[key];
            if (known && known.length > 8) {
                /* ── Popup picker trigger for large value lists ── */
                var hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.id   = 'add-f-' + catId + '-' + key;
                hidden.name = key;
                if (defVal) hidden.value = defVal;

                var trigger = document.createElement('div');
                trigger.id = 'add-trigger-' + catId + '-' + key;
                trigger.className = 'uk-input uk-form-small kb-picker-trigger';
                var summary = document.createElement('span');
                summary.className = 'kb-trigger-summary';
                if (defVal) { summary.textContent = defVal; }
                else { summary.textContent = 'Click to select…'; summary.style.color = '#bbb'; }
                var chev = document.createElement('span');
                chev.setAttribute('uk-icon', 'icon: chevron-down; ratio: 0.75');
                chev.style.cssText = 'flex-shrink:0; color:#aaa;';
                trigger.appendChild(summary);
                trigger.appendChild(chev);
                (function (cId, k) {
                    trigger.addEventListener('click', function () { window.kb_picker_open(cId, k); });
                }(catId, key));

                ctrl.appendChild(hidden);
                ctrl.appendChild(trigger);

            } else if (known && known.length > 0) {
                /* ── Inline tag chip multi-selector ── */
                var hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.id   = 'add-f-' + catId + '-' + key;
                hidden.name = key;

                var tagList = document.createElement('div');
                tagList.className = 'kb-tag-list';

                function syncHidden(tl, h) {
                    var vals = [];
                    tl.querySelectorAll('.kb-tag-selected').forEach(function (t) {
                        vals.push(t.dataset.value);
                    });
                    h.value = vals.join(', ');
                }

                known.forEach(function (v) {
                    var tag = document.createElement('span');
                    tag.className = 'kb-tag';
                    tag.dataset.value = v;
                    tag.textContent = v;
                    if (v === defVal) tag.classList.add('kb-tag-selected');
                    tag.addEventListener('click', function () {
                        tag.classList.toggle('kb-tag-selected');
                        syncHidden(tagList, hidden);
                    });
                    tagList.appendChild(tag);
                });
                syncHidden(tagList, hidden);

                /* Custom value — press Enter to add as a new chip */
                var customIn = document.createElement('input');
                customIn.type = 'text';
                customIn.className = 'uk-input uk-form-small kb-tag-custom-input';
                customIn.placeholder = 'Custom value — press Enter to add';
                customIn.addEventListener('keydown', function (e) {
                    if (e.key !== 'Enter') return;
                    e.preventDefault();
                    var v = customIn.value.trim();
                    if (!v) return;
                    var existing = tagList.querySelector('[data-value="' + v.replace(/"/g, '\\"') + '"]');
                    if (existing) {
                        existing.classList.add('kb-tag-selected');
                    } else {
                        var tag = document.createElement('span');
                        tag.className = 'kb-tag kb-tag-selected';
                        tag.dataset.value = v;
                        tag.textContent = v;
                        tag.addEventListener('click', function () {
                            tag.classList.toggle('kb-tag-selected');
                            syncHidden(tagList, hidden);
                        });
                        tagList.appendChild(tag);
                    }
                    customIn.value = '';
                    syncHidden(tagList, hidden);
                });

                ctrl.appendChild(tagList);
                ctrl.appendChild(customIn);
                ctrl.appendChild(hidden);

            } else {
                /* Free-form text for keys with no known values */
                var inp = document.createElement('input');
                inp.type = 'text'; inp.id = 'add-f-' + catId + '-' + key;
                inp.name = key; inp.className = 'uk-input uk-form-small';
                inp.value = defVal;
                if (!defVal) inp.placeholder = 'Enter ' + label.toLowerCase();
                ctrl.appendChild(inp);
            }
        }

        wrap.appendChild(lbl);
        wrap.appendChild(ctrl);
        return wrap;
    }

    /* Build the form for a given category */
    function buildForm(catId) {
        var form = document.getElementById('form-' + catId);
        form.innerHTML = '';

        /* Title — full width at top */
        var titleWrap = document.createElement('div');
        titleWrap.className = 'uk-margin-small';
        var titleLbl = document.createElement('label');
        titleLbl.className = 'uk-form-label';
        titleLbl.setAttribute('for', 'add-f-' + catId + '-__title__');
        titleLbl.innerHTML = '<strong>Title</strong>';
        var titleCtrl = document.createElement('div');
        titleCtrl.className = 'uk-form-controls';
        var titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.id   = 'add-f-' + catId + '-__title__';
        titleInput.name = '__title__';
        titleInput.className   = 'uk-input uk-form-small';
        titleInput.placeholder = 'Document title';
        titleCtrl.appendChild(titleInput);
        titleWrap.appendChild(titleLbl);
        titleWrap.appendChild(titleCtrl);
        form.appendChild(titleWrap);

        /* Divider */
        var hr = document.createElement('hr');
        hr.className = 'uk-divider-small uk-margin-small';
        form.appendChild(hr);

        /* Attribute fields in a 2-column grid (wide for tag-heavy keys) */
        var grid = document.createElement('div');
        grid.className = 'uk-grid-small uk-child-width-1-1 uk-child-width-1-2@m';
        grid.setAttribute('uk-grid', '');
        parseAttrs(catId).forEach(function (f) {
            var cell = document.createElement('div');
            cell.appendChild(makeRow(catId, f.key, f.key, f.def, f.key === 'Category'));
            grid.appendChild(cell);
        });
        form.appendChild(grid);
    }

    /* Collect form values and fill the skeleton template */
    function fillSkeleton(catId) {
        var form    = document.getElementById('form-' + catId);
        var result  = KB_SKEL[catId];
        var vals    = {};
        form.querySelectorAll('input[name]').forEach(function (el) {
            vals[el.name] = el.value.trim();
        });

        /* Replace title line */
        var title = vals['__title__'] || ('New ' + catId);
        result = result.replace(/^=\s+.+$/m, '= ' + title);

        /* Replace each :Key: line */
        Object.keys(vals).forEach(function (key) {
            if (key === '__title__' || !vals[key]) return;
            result = result.replace(
                new RegExp('^:' + key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ':\\s*.*$', 'm'),
                ':' + key + ': ' + vals[key]
            );
        });

        var dateEl  = document.getElementById('add-f-' + catId + '-Date');
        var dateStr = (dateEl && dateEl.value) ? dateEl.value : today();
        var filename = dateStr + '_' + slugify(title) + '.adoc';
        return { skeleton: result, filename: filename };
    }

    /* ── Public functions called from onclick handlers ── */
    window.kb_add_open = function (catId) {
        buildForm(catId);
        /* Reset to form step in case the modal was previously used */
        document.getElementById('add-form-' + catId).classList.remove('uk-hidden');
        document.getElementById('add-preview-' + catId).classList.add('uk-hidden');
        UIkit.modal('#modal-add-' + catId).show();
    };

    window.kb_add_generate = function (catId) {
        var titleEl = document.getElementById('add-f-' + catId + '-__title__');
        if (!titleEl || !titleEl.value.trim()) {
            UIkit.notification({ message: 'Please enter a title.', status: 'warning', timeout: 2500 });
            if (titleEl) titleEl.focus();
            return;
        }
        var out = fillSkeleton(catId);
        document.getElementById('add-skeleton-' + catId).value   = out.skeleton;
        document.getElementById('add-filename-' + catId).textContent = out.filename;
        document.getElementById('add-form-' + catId).classList.add('uk-hidden');
        document.getElementById('add-preview-' + catId).classList.remove('uk-hidden');
    };

    window.kb_add_back = function (catId) {
        document.getElementById('add-preview-' + catId).classList.add('uk-hidden');
        document.getElementById('add-form-' + catId).classList.remove('uk-hidden');
    };

    window.kb_add_copy = function (catId) {
        var el = document.getElementById('add-skeleton-' + catId);
        navigator.clipboard.writeText(el.value).catch(function () {
            el.select();
            document.execCommand('copy');
        });
        UIkit.notification({ message: 'Skeleton copied to clipboard', status: 'success', timeout: 2000 });
    };

    /* ── Shared picker modal ── */
    var KB_PICKER = { catId: null, key: null };

    var pickerEl = document.getElementById('kb-add-picker');

    function pickerShow() { pickerEl.style.display = 'flex'; }
    function pickerHide() { pickerEl.style.display = 'none'; }

    window.kb_picker_open = function (catId, key) {
        KB_PICKER = { catId: catId, key: key };
        document.getElementById('kb-picker-title').textContent = key;

        /* Current value from the hidden input */
        var hidden  = document.getElementById('add-f-' + catId + '-' + key);
        var current = hidden.value
            ? hidden.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean)
            : [];

        /* Build chip list: known values + any previously-custom ones not in known */
        var known = (KB_KEYS[key] || []).slice();
        current.forEach(function (cv) {
            if (known.indexOf(cv) === -1) known.push(cv);
        });

        var container = document.getElementById('kb-picker-chips');
        container.innerHTML = '';
        known.forEach(function (v) {
            var tag = document.createElement('span');
            tag.className = 'kb-tag';
            tag.dataset.value = v;
            tag.textContent = v;
            if (current.indexOf(v) !== -1) tag.classList.add('kb-tag-selected');
            tag.addEventListener('click', function () { tag.classList.toggle('kb-tag-selected'); });
            container.appendChild(tag);
        });

        document.getElementById('kb-picker-filter').value  = '';
        document.getElementById('kb-picker-custom').value  = '';
        window.kb_picker_filter();
        pickerShow();
        document.getElementById('kb-picker-filter').focus();
    };

    window.kb_picker_filter = function () {
        var q = document.getElementById('kb-picker-filter').value.toLowerCase();
        document.querySelectorAll('#kb-picker-chips .kb-tag').forEach(function (t) {
            t.style.display = (!q || t.dataset.value.toLowerCase().indexOf(q) !== -1) ? '' : 'none';
        });
    };

    window.kb_picker_clear = function () {
        document.querySelectorAll('#kb-picker-chips .kb-tag').forEach(function (t) {
            t.classList.remove('kb-tag-selected');
        });
    };

    window.kb_picker_done = function () {
        var catId = KB_PICKER.catId;
        var key   = KB_PICKER.key;
        if (!catId) return;

        var vals = [];
        document.querySelectorAll('#kb-picker-chips .kb-tag-selected').forEach(function (t) {
            vals.push(t.dataset.value);
        });

        /* Write back to hidden input */
        document.getElementById('add-f-' + catId + '-' + key).value = vals.join(', ');

        /* Update trigger summary */
        var trigger = document.getElementById('add-trigger-' + catId + '-' + key);
        if (trigger) {
            var summary = trigger.querySelector('.kb-trigger-summary');
            if (vals.length === 0) {
                summary.textContent = 'Click to select…';
                summary.style.color = '#bbb';
            } else {
                summary.style.color = '';
                summary.textContent = vals.length <= 3
                    ? vals.join(', ')
                    : vals.slice(0, 3).join(', ') + '  (+' + (vals.length - 3) + ')';
            }
        }

        pickerHide();
    };

    window.kb_picker_cancel = function () { pickerHide(); };

    /* Escape closes the picker without applying — stopPropagation prevents
       UIKit from also closing the parent full-screen modal. */
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && pickerEl.style.display === 'flex') {
            e.stopPropagation();
            pickerHide();
        }
    }, true);

    /* Custom value entry inside the picker */
    document.getElementById('kb-picker-custom').addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        var v = this.value.trim();
        if (!v) return;
        var container = document.getElementById('kb-picker-chips');
        var existing  = container.querySelector('[data-value="' + v.replace(/"/g, '\\"') + '"]');
        if (existing) {
            existing.classList.add('kb-tag-selected');
            existing.style.display = '';
        } else {
            var tag = document.createElement('span');
            tag.className = 'kb-tag kb-tag-selected';
            tag.dataset.value = v;
            tag.textContent = v;
            tag.addEventListener('click', function () { tag.classList.toggle('kb-tag-selected'); });
            container.appendChild(tag);
        }
        this.value = '';
        document.getElementById('kb-picker-filter').value = '';
        window.kb_picker_filter();
    });

})();
</script>
++++
