    <!-- PROPERTY BUTTON AND DIALOG :: START -->
    <a class="kb-cloud-item kb-cloud-key" style="--kb-weight: ${var['weight']};" href="#modal-full-${var['vfkey']}" data-uk-tooltip="${var['tooltip']}" data-uk-toggle>
        <span class="kb-cloud-word">${var['key']}</span>
    </a>
    <div id="modal-full-${var['vfkey']}" class="uk-modal-container" data-uk-modal>
        <div class="uk-modal-dialog" data-uk-overflow-auto>
            <button class="uk-modal-close-full uk-close-large uk-light uk-background-secondary uk-border-rounded" type="button" data-uk-close></button>
            <div class="uk-modal-header uk-light uk-background-secondary">
                <h2 class="uk-modal-title"><a href="${var['vfkey']}.html" class="uk-link-reset">${var['key']}</a></h2>
            </div>
            <div class="uk-modal-body">
${var['content'] | n}
            </div>
        </div>
    </div>
    <!-- PROPERTY BUTTON AND DIALOG :: END -->
