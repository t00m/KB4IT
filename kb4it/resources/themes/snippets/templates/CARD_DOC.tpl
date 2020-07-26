
                <!-- DOC_CARD.tpl :: START -->
                <div class="uk-card uk-card-default uk-width-1-1@m uk-card-hover" uk-scrollspy="target: > div; cls: uk-animation-fade; delay: 100" style="border:1px solid lightgray;">
                    <div class="uk-card-header">
                        <div class="uk-grid-small uk-flex-middle" uk-grid>
                            <div class="uk-width-expand">
                                <div class="uk-text-break uk-text-truncate uk-text-bold uk-margin-remove-bottom" uk-tooltip="${var['tooltip']}">
                                    ${var['title']}
                                </div>
                            </div>
                        </div>
                    </div>
${var['content']}
<!--
                <div class="uk-card uk-padding-small uk-padding-remove">
                    <div class="uk-flex uk-flex-center">
% for tag in var['tags']:
                            <span class="uk-meta">${tag} </span>
% endfor
                    </div>
                </div>
-->
                <!-- DOC_CARD.tpl :: END -->
