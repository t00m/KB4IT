++++
<!-- Template HTML_BODY_INDEX.tpl :: START -->
<!-- Blog Post :: START -->
<article class="post-card uk-card uk-card-default uk-card-body uk-margin-medium-bottom">
    % if len(var['post']['body'].strip()) > 0:
        <div class="uk-text-justify">
            ${var['post']['body'].strip()}
        </div>
    % endif

    <div class="uk-card-footer">
        <div class="uk-grid-big uk-flex-middle" uk-grid>
            <div class="uk-width-expand">
                <p class="uk-text-meta uk-margin-remove-top">
                    <span class="">Published by <a href="${var['post']['Author_0_Url']}">${var['post']['Author'][0]}</a> on
                    <a href="events_${var['post']['updated_day']}.html">${var['post']['updated_day_text']}</a>/<a href="events_${var['post']['updated_month']}.html">${var['post']['updated_month_text']}</a>/<a href="events_${var['post']['updated_year']}.html">${var['post']['updated_year_text']}</a><!-- at ${var['post']['updated_time']} -->
                    </span>
                    <br/>
                    <span>
                     Topics:
                        % for i, topic in enumerate(var['post']['Topic']):
                            <a href="Topic_${topic}.html">${topic}</a>${"," if i < len(var['post']['Topic'])-1 else ""}
                        % endfor
                    </span>
                    <br/>
                    <span>Tags:
                        % for i, tag in enumerate(var['post']['Tag']):
                            <a href="Tag_${tag}.html">${tag}</a>${"," if i < len(var['post']['Tag'])-1 else ""}
                        % endfor
                    </span>
                </p>
            </div>
        </div>
    </div>
</article>
<!-- Template HTML_BODY_INDEX.tpl :: END -->
++++
