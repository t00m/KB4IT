<main>
    <h1>${var['page']['title']}</h1>
% if var.get('starter', {}).get('date'):
    <p class="date">${var['starter']['date']}</p>
% endif
    ${var['source_html'] | n}
</main>
