<!-- PROFILE CARD :: START -->
<section class="kb-profile uk-card uk-card-default uk-card-body uk-margin">
    <p class="kb-profile-name uk-text-lead">${var['person']}</p>
% if var['alias_of']:
    <p class="kb-profile-alias">Profile of <a href="${var['alias_of']['href']}">${var['alias_of']['name']}</a></p>
% endif
% if var['rows']:
    <dl class="kb-profile-keys">
% for row in var['rows']:
        <dt>${row['key']}</dt>
% if row['href']:
        <dd><a href="${row['href']}">${row['value']}</a></dd>
% else:
        <dd>${row['value']}</dd>
% endif
% endfor
    </dl>
% endif
% if var['body']:
    <div class="kb-profile-body">${var['body'] | n}</div>
% endif
% if var['actions']['create'] or var['actions']['edit']:
    <div class="kb-profile-actions">
% if var['actions']['create']:
        <a class="uk-button uk-button-default uk-button-small" href="${var['actions']['create']}">Create profile</a>
% endif
% if var['actions']['edit']:
        <a class="uk-button uk-button-default uk-button-small" href="${var['actions']['edit']}">Edit profile</a>
% endif
    </div>
% endif
</section>
<!-- PROFILE CARD :: END -->
