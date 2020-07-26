
                <!-- CARD_DOC_DEFAULT.tpl :: START -->
                <div class="uk-card uk-card-default uk-width-1-1@m uk-card-hover" uk-scrollspy="target: > div; cls: uk-animation-fade; delay: 100" style="border:1px solid lightgray;">
                    <div class="uk-card-header">
                        <div class="uk-grid-small uk-flex-middle" uk-grid>
                            <div class="uk-width-expand">
                                <div class="uk-text-break uk-text-truncate uk-text-bold uk-margin-remove-bottom" uk-tooltip="${var['tooltip']}">
                                    ${var['title']}
                                </div>
                                <p class="uk-text-meta uk-margin-remove-top">
                                    <time datetime="${var['timestamp']}">${var['fuzzy_date']}</time>
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="uk-card uk-padding-small uk-padding-remove-bottom">
                        <div class="uk-flex uk-flex-right">
                            <ul class="uk-breadcrumb">
                                <li uk-tooltip="Category">${var['link_category']}</li>
                                <li uk-tooltip="Scope">${var['link_scope']}</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <!-- CARD_DOC_DEFAULT.tpl :: END -->
