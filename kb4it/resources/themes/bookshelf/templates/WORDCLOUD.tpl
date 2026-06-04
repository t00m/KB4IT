<div class="bk-wordcloud">
% for item in var['items']:
    <a href="${item['url']}" class="bk-cloud-word" style="font-size: ${0.8 + item.get('weight', 0.5) * 1.2}em;" title="${item['tooltip']}">${item['word']}</a>
% endfor
</div>
