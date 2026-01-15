<%
    from kb4it.core.util import get_human_datetime
    from kb4it.core.util import guess_datetime
    from kb4it.core.util import valid_filename
    timestamp = var['post']['Updated'][0]
    dt = guess_datetime(timestamp)
    var['post']['updated_human'] = get_human_datetime(dt)
    var['post']['updated_day_text'] = f"{dt.day:02d}"
    var['post']['updated_day'] = f"{dt.year:04d}{dt.month:02d}{dt.day:02d}"
    var['post']['updated_month_text'] = f"{dt.month:02d}"
    var['post']['updated_month'] = f"{dt.year:04d}{dt.month:02d}"
    var['post']['updated_year_text'] = f"{dt.year:04d}"
    var['post']['updated_year'] = f"{dt.year:04d}"
    var['post']['updated_time'] = f"{dt.hour.conjugate()}:{dt.minute.conjugate()}"
%>
++++
<!-- Template POST_ADOC_INDEX.tpl :: START -->
<!-- Blog Post :: START -->
<div class="uk-card uk-card-small uk-card-body post-card">
    <div class="uk-container uk-container-small">

        <!-- Header -->
        <header class="uk-margin-small-bottom uk-background-muted">
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
<!--
                            <li>
                                <span uk-icon="star"></span>
                                <span class="uk-margin-small-left">
                                % for i, topic in enumerate(var['post']['Topic']):
                                    <a href="Topic_${valid_filename(topic)}.html">${topic}</a>${"," if i < len(var['post']['Topic'])-1 else ""}
                                % endfor
                                </span>
                            </li>
                            <li>
                                <span uk-icon="tag"></span>
                                <span class="uk-margin-small-left">
                                % for i, tag in enumerate(var['post']['Tag']):
                                    <a href="Tag_${valid_filename(tag)}.html">${tag}</a>${"," if i < len(var['post']['Tag'])-1 else ""}
                                % endfor
                                </span>
                            </li>
-->
                            <!-- Metadata Button :: START -->
                            <li uk-tooltip="title: Document properties">
                                <span uk-icon="hashtag"></span>
                                <span class="uk-margin-small-left">
                                    <a href="#modal-metadata" uk-toggle>Metadata</a>
                                </span>
                                <div id="modal-metadata" class="uk-modal-full" uk-modal>
                                    <div class="uk-modal-dialog uk-height-viewport">
                                        <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                                        <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                                            <div class="uk-padding-large uk-background-muted">
                                                <div class="uk-text-lead uk-text-center uk-text-primary">Metadata</div>
                                                <div class="" style="border: 1px solid transparent;">${var['metadata']}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </li>
                            <!-- Metadata Button :: END -->
                            <!-- View Asciidoc Source Button :: START -->
                            <li uk-tooltip="title: Document source">
                                <span uk-icon="code"></span>
                                <span class="uk-margin-small-left">
                                    <a href="#modal-full-source" uk-toggle>Source</a>
                                </span>
                                <div id="modal-full-source" class="uk-modal-full" uk-modal>
                                    <div class="uk-modal-dialog uk-height-viewport">
                                        <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                                        <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                                            <div class="uk-padding-large uk-background-muted">
                                                <div class="uk-text-lead uk-text-center uk-text-danger">Source</div>
                                                <div class="uk-text-lead">${var['basename_adoc']}</div>
                                                <div class=""><textarea id="source-code" class="uk-width-1-1 uk-height-viewport">${var['source_adoc']}</textarea></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </li>
                            <!-- View Source Button :: END -->
                        </ul>
                    </div>
                    <!-- Tags and Topics -->
                </div>
            </div>
            <hr>
        </header>

        <!-- Body -->
        <article class="uk-article">
            ${var['post']['body'].strip()}
        </article>

        <!-- Footer -->
        <footer class="uk-margin-small-top uk-text-muted">
            <hr>
            <div class="uk-flex uk-flex-between uk-flex-middle">
            </div>
        </footer>
    </div>
</div>
<p></p>
<!-- Template POST_ADOC_INDEX.tpl :: END -->
++++
