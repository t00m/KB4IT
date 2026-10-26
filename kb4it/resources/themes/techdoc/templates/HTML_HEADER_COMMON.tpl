<% _hl = (var['repo'].get('markdown') or {}).get('highlight', 'client') %>
<!DOCTYPE html>
% if var['page'].get('exemplary'):
<html lang="en" class="kb-exemplary">
% else:
<html lang="en">
% endif
<head>
    <!-- PAGE METADATA :: START -->
    <meta charset="UTF-8">
    <title>${var['repo']['title']} - ${var['page']['title']}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="generator" content="KB4IT ${var['env']['APP']['build_version']}; ${var['theme'].get('identity', '')}">
    <!-- PAGE METADATA :: END -->
    <!-- SCRIPT FLAG :: START -->
    <!-- With JavaScript on, panels that a script switches are hidden until shown. -->
    <script>document.documentElement.classList.add('kb-js');</script>
    <!-- SCRIPT FLAG :: END -->
    <!-- STYLESHEETS :: START -->
% if _hl == 'client':
    <link rel="stylesheet" href="resources/themes/techdoc/framework/Highlight/styles/github-dark.css">
% elif _hl == 'pygments':
    <link rel="stylesheet" href="resources/pygments.css">
% endif
    <link rel="stylesheet" href="resources/themes/techdoc/framework/uikit/css/uikit.min.css" />
    <link rel="stylesheet" href="resources/themes/techdoc/framework/kb4it/css/print.css" type="text/css" media="print" />
    <link rel="stylesheet" href="resources/themes/techdoc/framework/kb4it/css/screen.css" />
    <!-- STYLESHEETS :: END -->
    <!-- LIBRARIES :: START -->
% if _hl == 'client':
    <script src="resources/themes/techdoc/framework/Highlight/highlight.js"></script>
% endif
    <script src="resources/themes/techdoc/framework/uikit/js/uikit.min.js"></script>
    <script src="resources/themes/techdoc/framework/uikit/js/uikit-icons.min.js"></script>
    <script src="resources/themes/techdoc/framework/datatables/js/jquery-3.5.1.js"></script>
    <script src="resources/themes/techdoc/framework/datatables/js/jquery.dataTables.min.js"></script>
    <script src="resources/themes/techdoc/framework/datatables/js/dataTables.uikit.min.js"></script>
    <!-- LIBRARIES :: END -->
    <script src="resources/themes/techdoc/framework/kb4it/js/page.js" defer></script>
    <script src="resources/themes/techdoc/framework/kb4it/js/blocks.js" defer></script>
% if var.get('has_quality'):
    <script defer src="quality-index.js"></script>
    <script defer src="resources/themes/techdoc/framework/kb4it/js/quality.js"></script>
% endif
    <!-- DATATABLES SETUP :: START -->
    <script class="init">
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
                    scrollX:        true,
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
    <!-- DATATABLES SETUP :: END -->
    <!-- PRINT FOOTER :: START -->
    <%
        # Print footer: the page title as a CSS string. Escape backslashes and quotes, and "<" so
        # "</style>" cannot close the block.
        _footer = ' '.join(str(var['page']['title']).split())
        _footer = _footer.replace('\\', '\\\\').replace('"', '\\"').replace('<', '\\3c ')
    %>
    <style media="print">
        @page { @bottom-left { content: "${_footer | n}"; } }
    </style>
    <!-- PRINT FOOTER :: END -->
</head>
<body>
<!-- PAGE :: START -->
<div class="uk-background-muted uk-height-viewport">
<!-- TOP BAR :: START -->
<div id="container-1" class="uk-container uk-container-center noprint">
    <div id="kb4it-menu" style="z-index: 980;" data-uk-sticky="show-on-up: true">
        <nav class="uk-navbar-container uk-border-rounded uk-card-hover uk-box-shadow-large" style="background-color: white;" data-uk-navbar>
            <!-- LOGO MENU :: START -->
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
                                    <a class="uk-link-heading" href="add.html"><span data-uk-icon="plus-circle"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Add document</span></a>
                                </li>
                                % endif
                                % if var.get('search_box'):
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="search.html"><span data-uk-icon="search"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Search</span></a>
                                </li>
                                % endif
                                % if var['editor'] or var.get('search_box'):
                                <li class="uk-nav-divider"></li>
                                % endif
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="events.html"><span data-uk-icon="calendar"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Events</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="bookmarks.html"><span data-uk-icon="bookmark"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Bookmarks</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="properties.html"><span data-uk-icon="database"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Properties</span></a>
                                    <div class="uk-navbar-dropdown" data-uk-dropdown="pos: right-top">
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
                                    <a class="uk-link-heading" href="stats.html"><span data-uk-icon="list"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Stats</span></a>
                                </li>
% if var['repo'].get('quality', True) is not False:
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="quality.html"><span data-uk-icon="star"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Quality</span></a>
                                </li>
% endif
                                <li class="uk-nav-divider"></li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="javascript:location.reload();"><span data-uk-icon="refresh"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Reload page</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="help.html"><span data-uk-icon="question"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">Help</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="about_app.html"><span data-uk-icon="info"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">About this app</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="about_kb4it.html"><span data-uk-icon="info"></span><span class="uk-padding-small uk-padding-remove-bottom uk-padding-remove-bottom-right uk-padding-remove-top">About KB4IT</span></a>
                                </li>
                            </ul>
                        </div>
                    </li>
                </ul>
            </div>
            <!-- LOGO MENU :: END -->
            <!-- PAGE TITLE :: START -->
            <!-- The title takes the room the left and right blocks leave, and is cut with an ellipsis. -->
            <div class="kb4it-navbar-title">
                <ul class="uk-navbar-nav">
                    <li>
                        <a class="uk-link-toggle uk-text-primary" href="#" title="${var['page']['title']}"><span id="kb4it-page-title" class="uk-text-primary uk-text-small">${var['page']['title']}</span></a>
<%
    _has_actions = '<a ' in var['actions']
    _has_toc = var['has_toc'] and len(var['toc']) > 0
%>
% if _has_actions or _has_toc:
                        <!-- TITLE MENU :: START -->
                        <!-- Shown on hover: the page actions in one row, then the table of contents. -->
                        <div class="uk-navbar-dropdown uk-navbar-dropdown-bottom-center kb4it-title-menu">
    % if _has_actions:
                            <!-- PAGE ACTIONS :: START -->
                            <div class="kb4it-page-actions noprint">
${var['actions'] | n}
                            </div>
                            <!-- PAGE ACTIONS :: END -->
    % endif
    % if _has_toc:
                            <!-- TITLE MENU CONTENTS :: START -->
                            <div class="uk-navbar-dropdown-nav kb4it-title-toc">
${var['toc'] | n}
                            </div>
                            <!-- TITLE MENU CONTENTS :: END -->
    % endif
                        </div>
                        <!-- TITLE MENU :: END -->
% endif
                    </li>
                </ul>
            </div>
            <!-- PAGE TITLE :: END -->
% if var.get('search_box'):
            <!-- SEARCH BUTTON :: START -->
            <div class="uk-navbar-right">
                <ul class="uk-navbar-nav noprint">
                    <li class="uk-card uk-card-small uk-card-hover uk-padding-small uk-padding-remove-vertical">
                        <a class="uk-link-heading" href="#kb4it-search-modal" title="Search (/ or Ctrl+K)" aria-label="Search" data-uk-toggle><span data-uk-icon="search"></span></a>
                    </li>
                </ul>
            </div>
            <!-- SEARCH BUTTON :: END -->
% endif
        </nav>
    </div>
% if var.get('search_box'):
    <!-- SEARCH DIALOG :: START -->
    <div id="kb4it-search-modal" class="kb4it-search-modal" data-uk-modal>
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
    <!-- SEARCH DIALOG :: END -->
% endif
</div>
<!-- TOP BAR :: END -->
<!-- CONTENT :: START -->
<div class="uk-container uk-container-center">
