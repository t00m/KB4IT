<!DOCTYPE Html>
<html lang="en">
<head>
    <title>KB4IT - ${var['page']['title']}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="Asciidoctor 2.0.10">
    <meta name="description" content="KB4IT document">
    <meta name="author" content="KB4IT by t00mlabs.net">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="resources/themes/techdoc/framework/uikit/css/uikit.min.css" />
    <link rel="stylesheet" href="resources/themes/techdoc/framework/kb4it/css/coderay-asciidoctor.css" />
    <link rel="stylesheet" href="resources/themes/techdoc/framework/kb4it/css/print.css" type="text/css" media="print" />
    <link rel="stylesheet" href="resources/themes/techdoc/framework/kb4it/css/screen.css" />
    <script src="resources/themes/techdoc/framework/uikit/js/uikit.min.js"></script>
    <script src="resources/themes/techdoc/framework/uikit/js/uikit-icons.min.js"></script>
    <script src="resources/themes/techdoc/framework/datatables/js/jquery-3.5.1.js"></script>
    <script src="resources/themes/techdoc/framework/datatables/js/jquery.dataTables.min.js"></script>
    <script src="resources/themes/techdoc/framework/datatables/js/dataTables.uikit.min.js"></script>
    <script type="text/javascript" class="init">
        $(document).ready(function() {
            $('#kb4it-datatable').DataTable( {
                dom: "<'bottom'flp><'clear'>i",
                serverSide: false,
                ordering: true,
                searching: true,
                //~ data:           data,
                deferRender:    true,
                scrollY:        400,
                scrollCollapse: false,
                scroller:       false,
                stateSave: false,
                paging:   false,
                info:     true,
                order: [[ 0, "desc" ]]
            } );
        } );
    </script>
</head>
<body>
<div class="uk-background-muted uk-height-viewport">
<div id="container-1" class="uk-container uk-container-center">
    <div id="print" class="uk-flex uk-flex-center"><span class="uk-text-lead">${var['page']['title']}</span></div>
    <div id="kb4it-menu" style="z-index: 980;" uk-sticky="show-on-up: true">
        <nav class="uk-navbar-container uk-border-rounded uk-card-hover uk-margin uk-box-shadow-large" style="background-color: white;" uk-navbar>
            <div class="uk-navbar-left noprint">
                <ul class="uk-navbar-nav">
                    <li class="uk-link-toggle uk-inline-clip uk-transition-toggle">
                        <a class="uk-logo uk-card uk-card-hover uk-transition-scale-up uk-transition-opaque" href="index.html">
                            <img src="${var['repo']['logo']}" alt="${var['repo']['logo_alt']}">
                        </a>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="#"><span uk-icon="database"></a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="events.html"><span class="uk-padding-small">Events</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="bookmarks.html"><span class="uk-padding-small">Bookmarks</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="properties.html"><span class="uk-padding-small">Properties</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="stats.html"><span class="uk-padding-small">Stats</span></a>
                                </li>
                                <li class="uk-link-toggle uk-nav-divider">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="Tag.html"><span class="uk-padding-small">Tags</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="Category.html"><span class="uk-padding-small">Category</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="Scope.html"><span class="uk-padding-small">Scopes</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="Topic.html"><span class="uk-padding-small">Topics</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="Author.html"><span class="uk-padding-small">Authors</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="Team.html"><span class="uk-padding-small">Teams</a>
                                </li>
                            </ul>
                        </div>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/new/${var['repo']['git_branch']}/${var['repo']['git_path']}" target="_blank"><span uk-icon="plus"></span></a>
                    </li>
                </ul>
                <ul class="uk-navbar-nav">
                    <!-- MENU CONTENTS :: START -->
${var['menu_contents']}
                    <!-- MENU CONTENTS :: END -->
                </ul>
                % if var['has_toc']:
                <ul class="uk-navbar-nav" uk-tooltip="title: Go to top">
                    <li class="uk-link-toggle">
                        <a class="uk-link-heading" href="" uk-totop></a>
                    </li>
                </ul>
                % endif
            </div>
            <div class="uk-navbar-center">
                <!-- DOCUMENT TITLE :: START -->
                <ul class="uk-navbar-nav">
                    <li>
                        <div class="uk-child-width-expand@s uk-text-center" uk-grid>
                            <div class="uk-card uk-card-small">
                                <div class="uk-card uk-card-small"><a class="uk-link-toggle uk-text-primary" href="#"><span class="uk-text-bolder uk-text-truncate">${var['page']['title']}</span></a></div>
                                <div class="uk-card uk-card-small">
% if var['has_toc']:
    ${var['actions']}
% endif
                                </div>
                            </div>
                    </li>
                </u>
                <!-- DOCUMENT TITLE :: END -->
            </div>

            <div class="uk-navbar-right noprint">
                <ul class="uk-navbar-nav">
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="javascript:location.reload();"><span uk-icon="refresh"></span></a>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="#"><span uk-icon="info"></a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="about_app.html"><span class="uk-padding-small">About this app</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="about_theme.html"><span class="uk-padding-small">About this theme</span></a>
                                </li>
                                <li class="uk-nav-divider"></li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="about_kb4it.html"><span class="uk-padding-small">About KB4IT</span></a>
                                </li>
                            </ul>
                        </div>
                    </li>
                </ul>
            </div>
        </nav>
    </div>
</div>
<div class="uk-container uk-container-center">
<div class="uk-container">
</div>
