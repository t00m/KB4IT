<!-- Template PAGE_ADMIN.tpl :: START -->
<div class="kb-sect1 uk-margin-small-bottom uk-card uk-card-small uk-card-body uk-border-rounded">
    <h2 class="kb-h2">Backup</h2>
    <div class="kb-section-body uk-container">
        <p class="kb-admin-intro">Download a snapshot of this repository. Both files are rebuilt on every build that compiles changes.</p>
        <div class="kb-admin-list">
% for item in var['backups']:
            <a class="kb-admin-card" href="${item['href']}" download>
                <span class="kb-admin-icon" uk-icon="icon: download; ratio: 1.4"></span>
                <span class="kb-admin-info">
                    <span class="kb-admin-name">${item['name']}</span>
                    <span class="kb-admin-desc">${item['description']}</span>
                    <span class="kb-admin-meta">${item['filename']} &middot; ${item['size']} &middot; ${item['timestamp']}</span>
                </span>
            </a>
% endfor
        </div>
    </div>
</div>
<!-- Template PAGE_ADMIN.tpl :: END -->
