    <!-- Button :: START -->
    <div>
        <div class="uk-card uk-card-small uk-border-rounded uk-card-hover uk-card-body uk-text-lead">
            <a class="uk-link-heading" href="#modal-full-${var['vfkey']}" uk-tooltip="${var['tooltip']}" uk-toggle><span style="font-size:${var['size']}pt;">${var['key']}</span></a>
            <div id="modal-full-${var['vfkey']}" class="uk-modal-container" uk-modal>
                <div class="uk-modal-dialog" uk-overflow-auto>
                    <button class="uk-modal-close-full uk-close-large uk-light uk-background-secondary" type="button" uk-close></button>
                    <div class="uk-modal-header uk-light uk-background-secondary">
                        <h2 class="uk-modal-title"><a href="${var['vfkey']}.html">${var['key']}</a></h2>
                    </div>
                    <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                        <div class="uk-padding-large">
${var['content']}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- Button :: END -->
