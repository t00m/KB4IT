<!-- PROPERTIES :: START -->
<div class="kb-props">
% for item in var['keys']:
    <div class="uk-grid-small kb-props-row" data-uk-grid>
        <div class="uk-width-expand" data-uk-leader>
            <a class="kb-props-key" href="${item['vfkey']}.html">${item['key']}</a>
        </div>
        <div class="kb-props-count">${item['values']} ${'value' if item['values'] == 1 else 'values'} <span class="kb-meta-sep">·</span> ${item['docs']} ${'document' if item['docs'] == 1 else 'documents'}</div>
    </div>
% endfor
</div>
<!-- PROPERTIES :: END -->
