<!-- WORDCLOUD.tpl :: START -->
<div class="uk-flex-center" uk-grid="parallax: 150">
% for item in var['items']:
    <!-- WORDCLOUD_ITEM.tpl :: START -->
    <div class="uk-container-xsmall uk-card uk-card-small uk-padding-small uk-margin-small">
        <a class="uk-link-heading" style="text-decoration: none;" href="${item['url']}" uk-tooltip="${item['tooltip']}">
            <span style="font-size:${item['size']}pt;">${item['word']}</span>
        </a>
    </div>
    <!-- WORDCLOUD_ITEM.tpl :: END -->
% endfor
</div>
<!-- WORDCLOUD.tpl :: END -->
