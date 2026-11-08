<div class="uk-flex uk-flex-wrap uk-flex-center">
% for item in var['items']:
    <a class="uk-margin-small-right" href="${item['url']}" title="${item['tooltip']}"><span style="font-size:${'%.2f' % (0.9 + item['weight'])}rem;">${item['word']}</span></a>
% endfor
</div>
