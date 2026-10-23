<!-- Template HTML_BODY_DOC.tpl :: START -->
<main class="kb-main">
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
        ${var['toc'] | n}
    </nav>
</details>
% endif

    <!-- This is the nav containing the toggling elements -->
    <ul class="uk-flex uk-flex-center uk-tab noprint uk-hidden" uk-switcher>
        <li><a href="#">Document</a></li>
    </ul>
    <!-- This is the container of the content items -->
    <ul class="uk-switcher uk-margin">
        <li class="uk-active"><div class="kb-content kb-content-${var.get('fmt', 'md')}">${var['source_html'] | n}</div></li>
    </ul>

% else:
    <div class="kb-content kb-content-${var.get('fmt', 'md')}">${var['source_html'] | n}</div>
% endif
</main>
<!-- Template HTML_BODY_DOC.tpl :: END -->
