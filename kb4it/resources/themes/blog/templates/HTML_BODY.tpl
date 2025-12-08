<!-- BODY :: START -->
<% title = var['page']['title'].strip() %>
<% title_len = len(title) %>
% if title_len > 0:
<div uk-tooltip="title: Edit post">
    <h3 class="uk-text-center"><span>${var['page']['title']}</span>
    <a class="uk-link-heading" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}/${var['basename_adoc']}" target="_blank"><span uk-icon="pencil"></span></a>
</div>
</h3>
% endif
${var['source_html']}
<!-- BODY :: END -->
