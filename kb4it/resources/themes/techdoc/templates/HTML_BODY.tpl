<!-- MAIN CONTENT :: START -->
<main class="kb-main${' kb-main-sidebar' if var.get('toc_sidebar') else ''}">
    <div class="kb-main-body">
% if var['has_toc']:
    <!-- PRINT HEADER :: START -->
    <!-- Shown only on paper: the document title above the contents. -->
    <div class="kb-print-header">
        <h1 class="kb-print-doc-title">${var['page']['title']}</h1>
    </div>
    <!-- PRINT HEADER :: END -->
${var.get('doc_header', '') | n}
${var.get('info_card', '') | n}
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
    </div>
% if var.get('toc_sidebar'):
    <!-- SIDE TABLE OF CONTENTS :: START -->
    <aside class="kb-toc-sidebar kb-noprint" aria-label="Table of contents">
        <nav class="kb-toc-nav kb-toc-sidebar-nav" data-uk-scrollspy-nav="closest: li; scroll: true; offset: 80">
            ${var['toc'] | n}
        </nav>
    </aside>
    <!-- SIDE TABLE OF CONTENTS :: END -->
% endif
</main>
<!-- MAIN CONTENT :: END -->
<!-- BACK TO TOP :: START -->
<a class="kb-totop kb-noprint" href="#" aria-label="Back to top"><span data-uk-icon="icon: arrow-up" aria-hidden="true"></span><span class="uk-hidden-visually">Back to top</span></a>
<!-- BACK TO TOP :: END -->
