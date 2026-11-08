<h1 class="uk-heading-small">${var['page']['title']}</h1>
${var.get('actions', '') | n}
% if var.get('starter', {}).get('tags'):
<p>
%   for tag in var['starter']['tags']:
    <a class="uk-label" href="${tag['url']}">${tag['name']}</a>
%   endfor
</p>
% endif
% if var.get('toc'):
<div class="uk-margin">${var['toc'] | n}</div>
% endif
${var['source_html'] | n}
