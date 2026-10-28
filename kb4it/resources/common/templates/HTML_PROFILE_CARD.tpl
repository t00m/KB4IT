<!-- PROFILE CARD :: START -->
<section class="kb-profile uk-card uk-card-default uk-card-body uk-margin">
    <h2 class="kb-profile-name">${var['person']}</h2>
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
    <div class="kb-profile-actions"></div>
</section>
<!-- PROFILE CARD :: END -->
