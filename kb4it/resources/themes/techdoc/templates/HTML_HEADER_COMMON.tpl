<% _hl = (var['repo'].get('markdown') or {}).get('highlight', 'client') %>
<!DOCTYPE html>
<html lang="en">
<head>
    <title>${var['repo']['title']} - ${var['page']['title']}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="KB4IT ${var['env']['APP']['version']}">
    <meta name="viewport" content="width=device-width, initial-scale=1">
% if _hl == 'client':
    <link rel="stylesheet" href="resources/themes/techdoc/framework/Highlight/styles/github-dark.css">
% elif _hl == 'pygments':
    <link rel="stylesheet" href="resources/pygments.css">
% endif
    <link rel="stylesheet" href="resources/themes/techdoc/framework/uikit/css/uikit.min.css" />
    <link rel="stylesheet" href="resources/themes/techdoc/framework/kb4it/css/print.css" type="text/css" media="print" />
    <link rel="stylesheet" href="resources/themes/techdoc/framework/kb4it/css/screen.css" />
% if _hl == 'client':
    <script src="resources/themes/techdoc/framework/Highlight/highlight.js"></script>
% endif
    <script src="resources/themes/techdoc/framework/uikit/js/uikit.min.js"></script>
    <script src="resources/themes/techdoc/framework/uikit/js/uikit-icons.min.js"></script>
    <script src="resources/themes/techdoc/framework/datatables/js/jquery-3.5.1.js"></script>
    <script src="resources/themes/techdoc/framework/datatables/js/jquery.dataTables.min.js"></script>
    <script src="resources/themes/techdoc/framework/datatables/js/dataTables.uikit.min.js"></script>
    <script type="text/javascript" class="init">
        $(document).ready(function() {
            $('.kb4it-datatable:not([data-dt-init])').each(function() {
                $(this).attr('data-dt-init', '1').DataTable({
                    dom: '<"kbfilter"flrtip>',
                    serverSide: false,
                    ordering: true,
                    searching: true,
                    deferRender:    true,
                    autoWidth:      false,
                    scrollY:        'calc(100vh - 200px)',
                    scrollCollapse: false,
                    scroller:       false,
                    stateSave: false,
                    paging:   false,
                    info:     true,
                    order: [[ 0, "desc" ]]
                });
            });
        });
    </script>
</head>
<body>
<!-- Template version ${var['env']['APP']['version']} -->
<div class="uk-background-muted uk-height-viewport">
<div id="container-1" class="uk-container uk-container-center noprint">
    <div id="kb4it-menu" style="z-index: 980;" uk-sticky="show-on-up: true">
        <nav class="uk-navbar-container uk-border-rounded uk-card-hover uk-box-shadow-large" style="background-color: white;" uk-navbar>
            <div class="uk-navbar-left">
                <ul class="uk-navbar-nav noprint">
                    <li class="uk-card uk-card-small uk-card-hover uk-padding-small uk-padding-remove-vertical">
                        <a class="uk-logo uk-transition-scale-up uk-transition-opaque" href="index.html">
                            <img src="${var['repo'].get('logo', 'resources/themes/techdoc/images/logo.svg')}" alt="${var['repo'].get('logo_alt') or var['repo']['title']}" width="24" height="24">
                        </a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                % if var['editor']:
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="add.html"><span uk-icon="plus-circle"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Add document</span></a>
                                </li>
                                <li class="uk-nav-divider"></li>
                                % endif
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="events.html"><span uk-icon="calendar"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Events</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="bookmarks.html"><span uk-icon="bookmark"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Bookmarks</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="properties.html"><span uk-icon="database"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Properties</span></a>
                                    <div class="uk-navbar-dropdown" uk-dropdown="pos: right-top">
                                        <ul class="uk-nav uk-navbar-dropdown-nav uk-padding-small uk-column-1-2">
            % for key in var['kb']['keys']['menu']:
                                            <li class="uk-link-toggle">
                                                <a class="uk-link-heading" href="${key['href']}.html"><span class="">${key['name']}</span></a>
                                            </li>
            % endfor
                                        </ul>
                                    </div>
                                </li>
                                <li class="uk-nav-divider"></li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="stats.html"><span uk-icon="list"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Stats</span></a>
                                </li>
                                <li class="uk-nav-divider"></li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="javascript:location.reload();"><span uk-icon="refresh"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Reload page</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="help.html"><span uk-icon="question"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Help</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="about_app.html"><span uk-icon="info"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">About this app</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="about_kb4it.html"><span uk-icon="info"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">About KB4IT</span></a>
                                </li>
                            </ul>
                        </div>
                    </li>
                </ul>
            </div>
            <!-- The title takes the room the left and right blocks leave, and is cut with an ellipsis. -->
            <div class="kb4it-navbar-title">
                <!-- DOCUMENT TITLE :: START -->
                <ul class="uk-navbar-nav">
                    <li>
                        <a class="uk-link-toggle uk-text-primary" href="#" title="${var['page']['title']}"><span id="kb4it-page-title" class="uk-text-primary uk-text-small">${var['page']['title']}</span></a>
<%
    _has_actions = '<a ' in var['actions']
    _has_toc = var['has_toc'] and len(var['toc']) > 0
%>
% if _has_actions or _has_toc:
                        <!-- Title menu: the page actions in one row, then the table of contents. -->
                        <div class="uk-navbar-dropdown uk-navbar-dropdown-bottom-center kb4it-title-menu">
    % if _has_actions:
                            <div class="kb4it-page-actions noprint">
${var['actions'] | n}
                            </div>
    % endif
    % if _has_toc:
                            <div class="uk-navbar-dropdown-nav kb4it-title-toc">
${var['toc'] | n}
                            </div>
    % endif
                        </div>
% endif
                    </li>
                </ul>
                <!-- DOCUMENT TITLE :: END -->
            </div>
% if var.get('search_box'):
            <div class="uk-navbar-right">
                <ul class="uk-navbar-nav noprint">
                    <li class="uk-card uk-card-small uk-card-hover uk-padding-small uk-padding-remove-vertical">
                        <a class="uk-link-heading" href="#kb4it-search-modal" title="Search (/ or Ctrl+K)" aria-label="Search" uk-toggle><span uk-icon="search"></span></a>
                    </li>
                </ul>
            </div>
% endif
        </nav>
    </div>
% if var.get('search_box'):
    <div id="kb4it-search-modal" class="kb4it-search-modal" uk-modal>
        <div class="uk-modal-dialog uk-modal-body">
            ${var['search_box'] | n}
        </div>
    </div>
    <script>
        (function () {
            var modal = document.getElementById("kb4it-search-modal");
            UIkit.util.on(modal, "shown", function () { document.getElementById("kb4it-search-input").focus(); });
            document.addEventListener("keydown", function (e) {
                // Keys typed in a field are left alone: Ctrl+K inserts a link in the Add page editor.
                var target = e.target, typing = target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName);
                var slash = e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey;
                var ctrlK = (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k";
                if (!typing && (slash || ctrlK)) { e.preventDefault(); UIkit.modal(modal).show(); }
            });
        })();
    </script>
% endif
</div>
<div class="uk-container uk-container-center">
    <div id="container-2" class="uk-container uk-container-center uk-flex uk-flex-center uk-hidden">
        <span class="uk-text-lead">${var['page']['title']}</span>
    </div>
