<!-- BODY :: START -->
<% title = var['page']['title'].strip() %>
<% title_len = len(title) %>
% if title_len > 0:
<div uk-tooltip="title: Edit post">
    <h2 class="uk-card-title uk-text-center">
        <a class="uk-link-toggle" href="${var['basename_adoc'].replace('adoc','html')}"><span class="uk-link-heading">${title}</span></a>
% if var['repo']['git'] == True:
        <a class="uk-link-heading" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}/${var['basename_adoc']}" target="_blank"><span uk-icon="pencil"></span></a>
% endif
    </h2>
</div>
% endif
${var['source_html']}
<!-- BODY :: END -->
