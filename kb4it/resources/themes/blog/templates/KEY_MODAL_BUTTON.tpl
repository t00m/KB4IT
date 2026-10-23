    <!-- Button :: START -->
    <div>
        <div class="uk-card uk-card-small uk-border-rounded uk-card-hover uk-card-body uk-text-lead">
            <a class="uk-link-heading" href="#modal-full-${var['vfkey']}" data-uk-tooltip="${var['tooltip']}" data-uk-toggle><span style="font-size:${var['size']}pt;">${var['key']}</span></a>
            <div id="modal-full-${var['vfkey']}" class="uk-modal-container" data-uk-modal>
                <div class="uk-modal-dialog" data-uk-overflow-auto>
                    <button class="uk-modal-close-full uk-close-large uk-light uk-background-secondary uk-border-rounded" type="button" data-uk-close></button>
                    <div class="uk-modal-header uk-light uk-background-secondary">
                        <div class="uk-modal-title uk-h2"><a href="${var['vfkey']}.html">${var['key']}</a></div>
                    </div>
                    <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" data-uk-grid>
                        <div class="uk-padding-large">
${var['content'] | n}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- Button :: END -->
