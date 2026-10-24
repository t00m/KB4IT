<!-- MAIN CONTENT :: START -->
<main class="kb-main">
% if var['has_toc']:
    <!-- PRINT HEADER :: START -->
    <!-- Shown only on paper: the document title above the contents. -->
    <div class="kb-print-header">
        <h1 class="kb-print-doc-title">${var['page']['title']}</h1>
    </div>
    <!-- PRINT HEADER :: END -->
${var.get('doc_header', '') | n}
    % if len(var['toc']) > 0:
    <!-- TABLE OF CONTENTS :: START -->
    <details id="kb-toc-inline" open class="kb-toc-panel">
        <summary class="kb-toc-summary">Table of Contents</summary>
        <nav class="kb-toc-nav">
            ${var['toc'] | n}
        </nav>
    </details>
    <!-- TABLE OF CONTENTS :: END -->
    % endif
    <!-- DOCUMENT BODY :: START -->
    <div class="kb-content kb-content-${var.get('fmt', 'md')} uk-margin" data-uk-lightbox="toggle: a.kb-zoom; animation: fade">
${var['source_html'] | n}
    </div>
    <!-- DOCUMENT BODY :: END -->
% else:
    <!-- PAGE BODY :: START -->
    <div class="kb-content kb-content-${var.get('fmt', 'md')}">
${var['source_html'] | n}
    </div>
    <!-- PAGE BODY :: END -->
% endif
</main>
<!-- MAIN CONTENT :: END -->
