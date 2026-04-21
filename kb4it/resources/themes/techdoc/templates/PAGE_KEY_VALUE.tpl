= ${var['title']}

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

++++
<div class="kb-kv-banner">
    <nav class="kb-kv-breadcrumb">
        <a href="properties.html">Properties</a>
        <span class="kb-kv-sep">›</span>
        <a href="${var['vfkey']}.html">${var['key']}</a>
        <span class="kb-kv-sep">›</span>
        <span class="kb-kv-current">${var['value']}</span>
    </nav>
    <div class="kb-kv-header">
        <span class="kb-kv-key-badge">${var['key']}</span>
        <span class="kb-kv-arrow">›</span>
        <span class="kb-kv-value-badge">${var['value']}</span>
        <span class="kb-kv-count">${len(var['doclist'])} doc${'s' if len(var['doclist']) != 1 else ''}</span>
    </div>
</div>
<div class="uk-container uk-overflow-auto">
${var['page']['dt_documents']}
</div>
++++
