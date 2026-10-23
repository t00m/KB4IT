<!-- ADD DOCUMENT :: START -->
<div class="uk-container kb-add">

    <div class="kb-add-note uk-alert-primary" data-uk-alert>
        <span data-uk-icon="icon: info; ratio: 0.9"></span>
        <strong>Note:</strong> This page saves or downloads the Markdown file for you.
        Click <em>Create</em> on any card, edit the template, then <em>Save</em> it
        (or <em>Copy</em> the text). Put the file in your repository's <strong>source</strong>
        folder and rebuild.
    </div>

% if var.get('git_ok'):
    <div class="kb-add-note uk-alert-primary" data-uk-alert>
        <span data-uk-icon="icon: git-branch; ratio: 0.9"></span>
        <strong>Online repository:</strong> The document source is hosted at
        <a href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}" target="_blank">
            ${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}
        </a>,  navigate to the source folder to upload your new file.
    </div>
% endif

    <!-- CATEGORY CARDS :: START -->
    <div class="uk-grid-small uk-child-width-1-2@s uk-child-width-1-4@m" data-uk-grid>
% for cat in var['page']['categories']:
        <div>
            <div class="uk-card uk-card-default uk-card-hover uk-card-small kb-add-card"
                 style="border-top: 3px solid ${cat['color']};">
                <div class="uk-card-header kb-add-card-header">
                    <h3 class="uk-card-title uk-margin-remove kb-add-card-title">
                        <span data-uk-icon="icon: ${cat['icon']}; ratio: 0.95"
                              style="color: ${cat['color']};"></span>
                        Add ${cat['name']}
                    </h3>
                </div>
                <div class="uk-card-body kb-add-card-body">
                    <p class="uk-margin-remove">${cat['description']}</p>
                </div>
                <div class="uk-card-footer kb-add-card-footer">
                    <button class="uk-button uk-button-small uk-button-primary"
                            data-kb-open="${cat['id']}">Create</button>
                </div>
            </div>
        </div>
% endfor
    </div>
    <!-- CATEGORY CARDS :: END -->

</div>
<!-- ADD DOCUMENT :: END -->

${var['page']['editor_dialogs'] | n}
