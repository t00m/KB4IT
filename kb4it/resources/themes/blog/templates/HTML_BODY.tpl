<% title = var['page']['title'].strip() %>
<% title_len = len(title) %>
% if title_len > 0:
    <h2 class="uk-card-title uk-text-center">
        <a class="uk-link-toggle" href="${var['basename_adoc'].replace('adoc','html')}"><span class="uk-link-heading">${title}</span></a>
    </h2>
% endif
<!-- BODY :: START -->
${var['source_html']}
<!-- BODY :: END -->
