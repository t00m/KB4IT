<!-- Template HTML_BODY_DOC.tpl :: START -->
% if var['has_toc']:

<!-- Print-only document header (hidden on screen) -->
<div class="kb-print-header">
    <h1 class="kb-print-doc-title">${var['page']['title']}</h1>
</div>

% if len(var['toc']) > 0:
<!-- Inline collapsible TOC -->
<details id="kb-toc-inline" open class="kb-toc-panel">
    <summary class="kb-toc-summary">Table of Contents</summary>
    <nav class="kb-toc-nav">
        ${var['toc']}
    </nav>
</details>
% endif

    <!-- This is the nav containing the toggling elements -->
    <ul class="uk-flex uk-flex-center uk-tab noprint uk-hidden" uk-switcher>
        <li><a href="#">Document</a></li>
    </ul>
    <!-- This is the container of the content items -->
    <ul class="uk-switcher uk-margin">
        <li class="uk-active">${var['source_html']}</li>
    </ul>

% if var['metadata']:
<!-- Document properties section at bottom (collapsed by default on screen) -->
<div class="kb-sect1 kb-sect1-collapsed uk-margin-small-bottom uk-card uk-card-small uk-card-body uk-border-rounded">
    <h2 class="kb-h2">Document Properties</h2>
    <div class="kb-section-body uk-container">
        ${var['metadata']}
    </div>
</div>
% endif

% else:
    ${var['source_html']}
% endif
<!-- Template HTML_BODY_DOC.tpl :: END -->
