<!-- ADD DOCUMENT :: START -->
<div class="kb-add">

    <div class="kb-add-note">
        <strong>Note:</strong> This page saves or downloads the Markdown file for you.
        Click <em>Create</em> on any card, edit the template, then <em>Save</em> it
        (or <em>Copy</em> the text). Put the file in your repository's <strong>source</strong>
        folder and rebuild.
    </div>

    <!-- CATEGORY CARDS :: START -->
    <div class="kb-add-cards">
% for cat in var['page']['categories']:
        <div class="kb-add-card" style="border-top: 3px solid ${cat['color']};">
            <h3 class="kb-add-card-title" style="color: ${cat['color']};">Add ${cat['name']}</h3>
            <p class="kb-add-card-body">${cat['description']}</p>
            <button class="kb-btn kb-btn-primary kb-btn-small" type="button"
                    data-kb-open="${cat['id']}">Create</button>
        </div>
% endfor
    </div>
    <!-- CATEGORY CARDS :: END -->

</div>
<!-- ADD DOCUMENT :: END -->

${var['page']['editor_dialogs'] | n}
