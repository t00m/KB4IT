                        <!-- DOC_CARD_AUTHOR.tpl :: START -->
                        <div data-title="${var['data-title']}" class="uk-card uk-width-1-3@m uk-card-hover" uk-scrollspy="target: > div; cls: uk-animation-fade; delay: 100" style="">
                            <div class="uk-card-header">
                                <div class="uk-grid-small uk-flex-middle" uk-grid>
                                    <div class="uk-width-expand">
                                        <div class="uk-text-break uk-text-truncate uk-text-bold uk-margin-remove-bottom" uk-tooltip="${var['tooltip']}">${var['title']}</div>
                                        <div class="uk-text-meta uk-margin-remove-top"><time datetime="${var['timestamp']}">${var['fuzzy_date']}</time> on ${var['scope']}</div>
                                    </div>
                                </div>
                            </div>
                            <div class="uk-card uk-padding-small uk-padding-remove-bottom">
                                <div class="uk-flex uk-flex-right">
                                    <ul class="uk-breadcrumb">
                                        <li uk-tooltip="Category">${var['category']}</li>
                                        <li uk-tooltip="Scope">${var['scope']}</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <!-- DOC_CARD_AUTHOR.tpl :: END -->
