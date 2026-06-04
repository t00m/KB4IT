<!-- PAGE_KEY_VALUE :: START -->
<div class="crumb">
    <a href="index.html">Library</a><span class="sep">&#9656;</span>
    <a href="properties.html">Properties</a><span class="sep">&#9656;</span>
    <a href="${var['vfkey']}.html">${var['key']}</a><span class="sep">&#9656;</span>
    <span class="here">${var['value']}</span>
</div>
<div class="bk-kv-head">
    <h1>${var['key']}: ${var['value']}</h1>
    <p class="sub">${len(var['doclist'])} document${'s' if len(var['doclist']) != 1 else ''}</p>
</div>
<div class="bk-panel">
    ${var['page']['dt_documents']}
</div>
<!-- PAGE_KEY_VALUE :: END -->
