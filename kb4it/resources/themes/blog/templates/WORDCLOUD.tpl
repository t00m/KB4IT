<!-- WORD CLOUD :: START -->
<div class="uk-flex-center" data-uk-grid="parallax: 150">
% for item in var['items']:
    <div class="uk-container-xsmall uk-card uk-card-small uk-padding-small uk-margin-small">
        <a class="uk-link-heading" style="text-decoration: none;" href="${item['url']}" data-uk-tooltip="${item['tooltip']}">
            <span style="font-size:${item['size']}pt;">${item['word']}</span>
        </a>
    </div>
% endfor
</div>
<!-- WORD CLOUD :: END -->
