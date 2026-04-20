<!-- WORDCLOUD.tpl :: START -->
<div class="kb-cloud">
% for item in var['items']:
    <a class="kb-cloud-item" style="--kb-weight: ${item['weight']};" href="${item['url']}" uk-tooltip="${item['tooltip']}">
        <span class="kb-cloud-word">${item['word']}</span>
    </a>
% endfor
</div>
<!-- WORDCLOUD.tpl :: END -->
