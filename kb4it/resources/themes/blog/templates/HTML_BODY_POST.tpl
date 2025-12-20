<%
    from kb4it.core.util import get_human_datetime
    from kb4it.core.util import guess_datetime
    timestamp = var['post']['Updated'][0]
    dt = guess_datetime(timestamp)
    var['post']['updated_human'] = get_human_datetime(dt)
    var['post']['updated_day_text'] = f"{dt.day}"
    var['post']['updated_day'] = f"{dt.year}{dt.month}{dt.day}"
    var['post']['updated_month_text'] = f"{dt.month}"
    var['post']['updated_month'] = f"{dt.year}{dt.month}"
    var['post']['updated_year_text'] = f"{dt.year}"
    var['post']['updated_year'] = f"{dt.year}"
    var['post']['updated_time'] = f"{dt.hour.conjugate()}:{dt.minute.conjugate()}"
%>
<!-- Template HTML_BODY_INDEX.tpl :: START -->
<!-- Blog Post :: START -->
<div class="uk-card uk-card-small uk-card-body post-card">
    <div class="uk-container uk-container-small">

        <!-- Header -->
        <header class="uk-margin-small-bottom">
            <div class="uk-flex uk-flex-middle uk-margin-bottom">
                <div class="uk-width">
                    <h5 class="uk-card-title uk-margin-remove uk-text-center">
                        <a class="uk-link-toggle" href="${var['post']['Title_Url']}">
                            <span class="uk-link-heading">${var['post']['Title']}</span>
                        </a>
                    </h5>
                    <div class="uk-width">
                        <ul class="uk-subnav uk-subnav-divider uk-margin-small-top uk-flex-center uk-text-meta">
                            <li>
                                <span uk-icon="user"></span>
                                <span class="uk-margin-small-left"><a href="${var['post']['Author_0_Url']}">${var['post']['Author'][0]}</a></span>
                            </li>
                            <li>
                                <span uk-icon="calendar"></span>
                                <span class="uk-margin-small-left"><a href="events_${var['post']['updated_day']}.html">${var['post']['updated_day_text']}</a>/<a href="events_${var['post']['updated_month']}.html">${var['post']['updated_month_text']}</a>/<a href="events_${var['post']['updated_year']}.html">${var['post']['updated_year_text']}</a></span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <hr>
        </header>

        <!-- Body -->
        <article class="uk-article">
            <!-- BODY :: START -->
            ${var['source_html']}
            <!-- BODY :: END -->
        </article>

        <!-- Footer -->
        <footer class="uk-margin-small-top uk-text-muted">
            <hr>
            <div class="uk-flex uk-flex-between uk-flex-middle">

                <div class="uk-width">
                    <ul class="uk-subnav uk-subnav-divider uk-margin-small-top uk-flex-center uk-text-meta">
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
        </footer>
    </div>
</div>
<p></p>
<!-- Template HTML_BODY_POST.tpl :: END -->
