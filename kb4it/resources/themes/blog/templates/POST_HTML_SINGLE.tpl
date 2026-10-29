<%
    from kb4it.core.util import get_human_datetime
    from kb4it.core.util import guess_datetime
    from kb4it.core.util import valid_filename
    sort_by = var['repo']['sort']
    timestamp = (var['post'].get(sort_by) or [None])[0]
    dt = guess_datetime(timestamp) if timestamp else None
    # An undated post has no calendar line (the theme logs DOC_UNDATED for it).
    var['post']['dated'] = dt is not None
    if dt is not None:
        var['post']['updated_human'] = get_human_datetime(dt)
        var['post']['updated_day_text'] = f"{dt.day:02d}"
        var['post']['updated_day'] = f"{dt.year:04d}{dt.month:02d}{dt.day:02d}"
        var['post']['updated_month_text'] = f"{dt.month:02d}"
        var['post']['updated_month'] = f"{dt.year:04d}{dt.month:02d}"
        var['post']['updated_year_text'] = f"{dt.year:04d}"
        var['post']['updated_year'] = f"{dt.year:04d}"
        var['post']['updated_time'] = f"{dt.hour:02d}:{dt.minute:02d}"
%>
<!-- MAIN CONTENT :: START -->
<main class="kb-main">
<!-- POST :: START -->
<article class="uk-card uk-card-small uk-card-body post-card">
    <div class="uk-container uk-container-small">
        <!-- POST HEADER :: START -->
        <header class="uk-margin-small-bottom">
            <div class="uk-flex uk-flex-middle uk-margin-bottom">
                <div class="uk-width uk-margin-top">
                    <h1 class="uk-card-title uk-margin-remove uk-text-center">
                        <a class="uk-link-toggle" href="${var['post']['Title_Url']}">
                            <span class="uk-link-heading">${var['post']['Title']}</span>
                        </a>
                    </h1>
                    <div class="uk-width uk-margin-top">
                        <ul class="uk-subnav uk-subnav-divider uk-margin-small-top uk-flex-center uk-text-meta">
% if 'Author_0_Url' in var['post']:
                            <li>
                                <span data-uk-icon="user"></span>
% if var['post'].get('Author_0_Tip'):
                                <span class="uk-margin-small-left"><a href="${var['post']['Author_0_Url']}" title="${var['post']['Author_0_Tip']}" data-uk-tooltip>${var['post']['Author'][0]}</a></span>
% else:
                                <span class="uk-margin-small-left"><a href="${var['post']['Author_0_Url']}">${var['post']['Author'][0]}</a></span>
% endif
                            </li>
% endif
% if var['post']['dated']:
                            <!-- LAST UPDATE :: START -->
                            <li data-uk-tooltip="title: Document last update">
                                <span data-uk-icon="calendar"></span>
                                <span class="uk-margin-small-left"><a href="events_${var['post']['updated_day']}.html">${var['post']['updated_day_text']}</a>/<a href="events_${var['post']['updated_month']}.html">${var['post']['updated_month_text']}</a>/<a href="events_${var['post']['updated_year']}.html">${var['post']['updated_year_text']}</a></span>
                            </li>
                            <!-- LAST UPDATE :: END -->
% endif
                            <!-- PROPERTIES BUTTON AND DIALOG :: START -->
                            <li data-uk-tooltip="title: Document properties">
                                <span data-uk-icon="hashtag"></span>
                                <span class="uk-margin-small-left">
                                    <a href="#modal-metadata" data-uk-toggle>Metadata</a>
                                </span>
                                <div id="modal-metadata" class="uk-modal-full" data-uk-modal>
                                    <div class="uk-modal-dialog uk-height-viewport">
                                        <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" data-uk-close></button>
                                        <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" data-uk-grid>
                                            <div class="uk-padding-large uk-background-muted">
                                                <div class="uk-text-lead uk-text-center uk-text-primary">Metadata</div>
                                                <div class="" style="border: 1px solid transparent;">${var['metadata'] | n}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </li>
                            <!-- PROPERTIES BUTTON AND DIALOG :: END -->
                            <!-- SOURCE BUTTON AND DIALOG :: START -->
                            <li data-uk-tooltip="title: Document source">
                                <span data-uk-icon="code"></span>
                                <span class="uk-margin-small-left">
                                    <a href="#modal-full-source" data-uk-toggle>Source</a>
                                </span>
                                <div id="modal-full-source" class="uk-modal-full" data-uk-modal>
                                    <div class="uk-modal-dialog uk-height-viewport">
                                        <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" data-uk-close></button>
                                        <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" data-uk-grid>
                                            <div class="uk-padding-large uk-background-muted">
                                                <div class="uk-text-lead uk-text-center uk-text-danger">Source</div>
                                                <div class="uk-text-lead">${var['basename_md']}</div>
                                                <div class=""><textarea id="source-code" class="uk-width-1-1 uk-height-viewport">${var['source_md']}</textarea></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </li>
                            <!-- SOURCE BUTTON AND DIALOG :: END -->
% if var.get('git_ok'):
                            <li data-uk-tooltip="title: Edit document">
                                <span data-uk-icon="pencil"></span>
                                <span class="uk-margin-small-left">
                                    <a class="" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/edit/${var['repo']['git_branch']}/${var['repo']['git_path']}/${var['basename_md']}" target="_blank" data-uk-toggle>Edit</a>
                                </span>
                            </li>
% endif
                        </ul>
                    </div>
                </div>
            </div>
        </header>
        <!-- POST HEADER :: END -->

        <!-- POST BODY :: START -->
        <div class="uk-article">
            ${var['source_html'] | n}
        </div>
        <!-- POST BODY :: END -->

        <!-- POST FOOTER :: START -->
        <footer class="uk-margin-small-top uk-text-muted">
            <div class="uk-flex uk-flex-between uk-flex-middle">
            </div>
        </footer>
        <!-- POST FOOTER :: END -->
    </div>
</article>
<!-- POST :: END -->
<p></p>
</main>
<!-- MAIN CONTENT :: END -->
