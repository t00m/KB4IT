                        <!-- DOC_CARD.tpl :: START -->
                        <div data-title="${var['data-title']}" class="uk-card uk-card-small uk-card-hover" uk-scrollspy="target: > div; cls: uk-animation-fade; delay: 100" style="">
                            <div class="uk-card-header">
                                <div class="uk-grid-small uk-flex-middle" uk-grid>
                                    <div class="uk-width-expand">
                                        <div class="uk-text-break uk-text-truncate uk-text-bold uk-margin-remove-bottom" uk-tooltip="${var['tooltip']}">${var['title']}</div>
                                        <div class="uk-text-meta uk-margin-remove-top"><time datetime="${var['timestamp']}">${var['fuzzy_date']}</time> on ${var['category']}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <!-- DOC_CARD.tpl :: END -->
