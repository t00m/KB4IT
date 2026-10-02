<!-- Actions -->
% if not var['SystemPage']:
% if var['repo'].get('git'):
<a class="icon-btn" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}/${var['basename_md']}" target="_blank" title="Edit">Edit</a>
% endif
% endif
