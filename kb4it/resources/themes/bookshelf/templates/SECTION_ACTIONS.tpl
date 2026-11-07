<!-- Actions -->
% if not var['SystemPage']:
% if var.get('edit_url'):
<a class="icon-btn" href="${var['edit_url']}" target="_blank" title="Edit">Edit</a>
% endif
% endif
