<!-- MAIN CONTENT :: START -->
<main class="kb-main">
% if '<h1' not in var['source_html']:
<h1 class="uk-hidden-visually">${var['page']['title']}</h1>
% endif
${var['source_html'] | n}
</main>
<!-- MAIN CONTENT :: END -->
