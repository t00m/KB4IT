                        <!-- DOC_CARD.tpl :: START -->
                        <div class="uk-card uk-card-default uk-width-1-1@m uk-card-hover" uk-scrollspy="target: > div; cls: uk-animation-fade; delay: 100" style="border:1px solid lightgray;">
                            <div class="uk-card-header">
                                <div class="uk-grid-small uk-flex-middle" uk-grid>
                                    <div class="uk-width-auto">
                                        <a href="%s"><img class="uk-border-circle" width="48" height="48" src="%s" uk-tooltip="%s"></a>
                                    </div>
                                    <div class="uk-width-expand">
                                        <div class="uk-text-break uk-text-truncate uk-text-bold uk-margin-remove-bottom">%s</div>
                                        <p class="uk-text-meta uk-margin-remove-top"><time datetime="%s">%s</time></p>
                                    </div>
                                </div>
                            </div>
                            <div class="uk-card-footer uk-padding-remove-bottom">
                                <div class="uk-flex uk-flex-right">
                                    <ul class="uk-breadcrumb">
                                        <li class="uk-text-uppercase" uk-tooltip="Category">%s</li>
                                        <li class="uk-text-uppercase" uk-tooltip="Scope">%s</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <!-- DOC_CARD.tpl :: END -->
