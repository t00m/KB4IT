<!-- BODY :: START -->
<div uk-tooltip="title: Edit post">
    <h3 class="uk-text-center"><span>${var['page']['title']}</span>
    <a class="uk-link-heading" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}/${var['basename_adoc']}" target="_blank"><span uk-icon="pencil"></span></a>
</div>
</h3>
${var['source_html']}
<!-- BODY :: END -->
