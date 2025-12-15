++++
<!-- Template HTML_BODY_INDEX.tpl :: START -->
<!-- Blog Post :: START -->
<div class="uk-card uk-card-small uk-card-body post-card">
    <div class="uk-container uk-container-small">

        <!-- Header -->
        <header class="uk-margin-small-bottom">
            <div class="uk-flex uk-flex-middle uk-margin-bottom">
                <div>
                    <h2 class="uk-heading-small uk-margin-remove">
                        <a class="uk-link-toggle" href="${var['post']['Title_Url']}">
                            <span class="uk-link-heading">${var['post']['Title']}</span>
                        </a>
                    </h2>

                    <ul class="uk-subnav uk-subnav-divider uk-margin-small-top">
                        <li>
                            <span uk-icon="user"></span>
                            <span class="uk-margin-small-left"><a href="${var['post']['Author_0_Url']}">${var['post']['Author'][0]}</a></span>
                        </li>
                        <li>
                            <span uk-icon="calendar"></span>
                            <span class="uk-margin-small-left"><a href="events_${var['post']['updated_day']}.html">${var['post']['updated_day_text']}</a>/<a href="events_${var['post']['updated_month']}.html">${var['post']['updated_month_text']}</a>/<a href="events_${var['post']['updated_year']}.html">${var['post']['updated_year_text']}</a></span>
                        </li>
                        <li>
                            <span uk-icon="tag"></span>
                            <span class="uk-margin-small-left">
                        % for i, tag in enumerate(var['post']['Tag']):
                            <a href="Tag_${tag}.html">${tag}</a>${"," if i < len(var['post']['Tag'])-1 else ""}
                        % endfor
                            </span>
                        </li>
                    </ul>
                </div>
            </div>

            <hr>
        </header>

        <!-- Body -->
        <article class="uk-article">
            ${var['post']['body'].strip()}
        </article>

        <!-- Footer
        <footer class="uk-margin-small-top uk-text-muted">
            <hr>
            <div class="uk-flex uk-flex-between uk-flex-middle">
            </div>
        </footer>
        -->
    </div>
</div>
<p></p>
<!-- Template HTML_BODY_INDEX.tpl :: END -->
++++
