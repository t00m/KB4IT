<%
    groups = var['filters']
    diagram = var['kind'] == 'diagram'
    noun, nouns = ('diagram', 'diagrams') if diagram else ('image', 'images')
    tag = 'DIAGRAMS' if diagram else 'GALLERY'
%>
<!-- ${tag} PAGE :: START -->
<div class="uk-container kb-gallery-page"${' data-kb4it-mermaid="page"' if diagram and var['items'] else '' | n}>
% if var['items']:
    <div class="kb-gal">
        <!-- ${tag} CONTENT :: START -->
        <div class="kb-gal-main">
            <p class="kb-gal-status" id="kb-gal-status" aria-live="polite">${var['items']} ${noun if var['items'] == 1 else nouns} in ${var['docs']} ${'document' if var['docs'] == 1 else 'documents'}. Choose a property on the right to show its ${nouns}.</p>
            <div class="kb-gal-grid uk-grid-small uk-child-width-1-2 uk-child-width-1-3@s uk-child-width-1-4@l" id="kb-gal-grid" data-uk-grid="masonry: pack" hidden></div>
            <noscript><p class="kb-gal-status">This page needs JavaScript to show the ${nouns}.</p></noscript>
        </div>
        <!-- ${tag} CONTENT :: END -->
        <!-- ${tag} FILTERS :: START -->
        <aside class="kb-gal-panel noprint" aria-label="Filter ${nouns}">
            <div class="kb-gal-panel-head">
                <strong>Filters</strong>
                <button type="button" class="uk-button uk-button-link kb-gal-clear" id="kb-gal-clear" hidden>Clear all</button>
            </div>
% if diagram:
            <label class="uk-hidden-visually" for="kb-gal-text">Words of the title, the section or the diagram</label>
            <input class="uk-input uk-form-small kb-gal-text" id="kb-gal-text" type="search" placeholder="Title, section or diagram text" autocomplete="off">
% else:
            <label class="uk-hidden-visually" for="kb-gal-text">Words of the title or caption</label>
            <input class="uk-input uk-form-small kb-gal-text" id="kb-gal-text" type="search" placeholder="Title or caption" autocomplete="off">
% endif
            <div class="kb-gal-keys">
%     for group in groups:
                <button type="button" class="kb-gal-key" data-key="${group['key']}" aria-haspopup="dialog">
                    <span class="kb-gal-key-name">${group['key']}</span>
                    <span class="kb-gal-key-info">${len(group['values'])} ${'value' if len(group['values']) == 1 else 'values'}</span>
                </button>
%     endfor
            </div>
            <div class="kb-gal-chips" id="kb-gal-chips"></div>
        </aside>
        <!-- ${tag} FILTERS :: END -->
    </div>
    <!-- ${tag} VALUES DIALOG :: START -->
    <div id="kb-gal-modal" class="kb-gal-modal" data-uk-modal>
        <div class="uk-modal-dialog">
            <button class="uk-modal-close-default" type="button" data-uk-close aria-label="Close"></button>
            <div class="uk-modal-header">
                <p class="uk-modal-title" id="kb-gal-modal-title"></p>
                <div class="kb-gal-modal-find">
                    <label class="uk-hidden-visually" for="kb-gal-modal-find">Find a value</label>
                    <input class="uk-input uk-form-small" id="kb-gal-modal-find" type="search" placeholder="Find a value" autocomplete="off">
                </div>
            </div>
            <div class="uk-modal-body kb-gal-modal-values" id="kb-gal-modal-values"></div>
            <div class="uk-modal-footer uk-text-right">
                <button class="uk-button uk-button-default uk-button-small" type="button" id="kb-gal-modal-none">None</button>
                <button class="uk-button uk-button-primary uk-button-small uk-modal-close" type="button">Show ${nouns}</button>
            </div>
        </div>
    </div>
    <!-- ${tag} VALUES DIALOG :: END -->
    <script type="application/json" id="kb-gal-data">${var['json'] | n}</script>
    <script src="resources/themes/techdoc/framework/kb4it/js/gallery.js" defer></script>
% elif diagram:
    <p class="kb-gal-status">No document has a diagram yet. Add one with a <code>```mermaid</code> code block; see the <a href="https://mermaid.js.org/">Mermaid documentation</a>.</p>
% else:
    <p class="kb-gal-status">No document shows an image yet. Add one with <code>![What it shows](resources/images/file.png)</code> and the file in <code>source/resources/images/</code>.</p>
% endif
</div>
<!-- ${tag} PAGE :: END -->
