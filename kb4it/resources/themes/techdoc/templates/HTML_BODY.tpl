<!-- Template HTML_BODY_DOC.tpl :: START -->
% if var['has_toc']:

<!-- Print-only document header (hidden on screen) -->
<div class="kb-print-header">
    <h1 class="kb-print-doc-title">${var['page']['title']}</h1>
</div>

<!-- Document metadata (hidden on screen, shown in print) -->
<div id="kb4it-doc-metadata" class="uk-hidden" style="border: 1px solid transparent;">${var['metadata']}</div>

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
<!-- <li><a href="#">Related</a></li> -->
    </ul>
    <!-- This is the container of the content items -->
    <ul class="uk-switcher uk-margin">
        <li class="uk-active">${var['source_html']}</li>
<!-- <li>var['related']</li> -->
    </ul>
% else:
    ${var['source_html']}
% endif
<!-- Template HTML_BODY_DOC.tpl :: END -->
