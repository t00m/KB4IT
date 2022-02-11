<!-- Template SECTION_ACTIONS.tpl :: START -->
% if var['has_toc']:
<div class="uk-flex uk-flex-center">
    <ul class="uk-iconnav">
        <li><a href="https://${var['conf']['git_server']}/${var['conf']['git_user']}/${var['conf']['git_repo']}/edit/${var['conf']['git_branch']}/${var['conf']['git_path']}/${var['basename_adoc']}" target="_blank"><span uk-icon="icon: pencil; ratio: 1.0;"></span></span></a></li>
        <li><a onclick="window.print()"><span uk-icon="icon: print; ratio: 1.0;"></span></a></li>
        <li><a href="#" uk-icon="icon: copy"></a></li>
        <li><a href="#"><span uk-icon="icon: bag"></span> (2)</a></li>
    </ul>
</div>
% endif
<!-- Template SECTION_ACTIONS.tpl :: END -->


