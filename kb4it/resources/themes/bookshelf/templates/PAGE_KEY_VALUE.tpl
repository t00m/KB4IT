<!-- PROPERTY VALUE :: START -->
<!-- BREADCRUMB :: START -->
<div class="crumb">
    <a href="index.html">Library</a><span class="sep">&#9656;</span>
    <a href="properties.html">Properties</a><span class="sep">&#9656;</span>
    <a href="${var['vfkey']}.html">${var['key']}</a><span class="sep">&#9656;</span>
    <span class="here">${var['value']}</span>
</div>
<!-- BREADCRUMB :: END -->
<div class="bk-kv-head">
    <h1>${var['key']}: ${var['value']}</h1>
    <p class="sub">${len(var['doclist'])} document${'s' if len(var['doclist']) != 1 else ''}</p>
</div>
${var.get('profile_card', '') | n}
<!-- DOCUMENTS TABLE :: START -->
<div class="bk-panel">
    ${var['page']['dt_documents'] | n}
</div>
<!-- DOCUMENTS TABLE :: END -->
<!-- PROPERTY VALUE :: END -->
