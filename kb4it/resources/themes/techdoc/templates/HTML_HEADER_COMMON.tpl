<!DOCTYPE html>
<html lang="en">
<head>
    <title>${var['repo']['title']} - ${var['page']['title']}</title>
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
    <link rel="stylesheet" href="resources/themes/techdoc/framework/TimelineJS/css/timeline.css" />
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
<!-- Template version ${var['env']['APP']['version']} -->
<div class="uk-background-muted uk-height-viewport">
<div id="container-1" class="uk-container uk-container-center">
    <div id="print" class="uk-flex uk-flex-center"><span class="uk-text-lead">${var['page']['title']}</span></div>
    <div id="kb4it-menu" style="z-index: 980;" uk-sticky="show-on-up: true">
        <nav class="uk-navbar-container uk-border-rounded uk-card-hover uk-margin uk-box-shadow-large" style="background-color: white;" uk-navbar>
            <div class="uk-navbar-left noprint">
                <ul class="uk-navbar-nav">
                    <li class="uk-link-toggle uk-inline-clip uk-transition-toggle">
                        <a class="uk-logo uk-card uk-card-hover uk-transition-scale-up uk-transition-opaque" href="index.html">
                            <img src="${var['repo']['logo']}" alt="${var['repo']['logo_alt']}" width="24px" height="24px">
                        </a>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="#"><span uk-icon="database"></span></a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
% for key in var['kb']['keys']['menu']:
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="${key}.html"><span class="">  By ${key}</span></a>
                                </li>
% endfor
                            </ul>
                        </div>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="#"><span uk-icon="star"></span></a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="events.html"><span class="">Events</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="bookmarks.html"><span class="">Bookmarks</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="properties.html"><span class="">Properties</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="stats.html"><span class="">Stats</span></a>
                                </li>
                            </ul>
                        </div>
                    </li>
% if var['repo']['git'] == True:
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="${var['repo']['git_server']}/${var['repo']['git_user']}/${var['repo']['git_repo']}/new/${var['repo']['git_branch']}/${var['repo']['git_path']}" target="_blank"><span uk-icon="plus"></span></a>
                    </li>
% endif
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
                                <a class="uk-link-toggle uk-text-primary" href="#"><span class="uk-text-primary uk-text-small uk-text-truncate">${var['page']['title']}</span></a>
% if var['has_toc']:
                                <div class="uk-navbar-dropdown uk-navbar-dropdown-bottom-center">
                                    <ul class="uk-nav uk-navbar-dropdown-nav">
    ${var['actions']}
                                    </ul>
                                </div>
% endif
                            </div>
                        </div>
                    </li>
                </ul>
                <!-- DOCUMENT TITLE :: END -->
            </div>

            <div class="uk-navbar-right noprint">
                <ul class="uk-navbar-nav">
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="javascript:location.reload();"><span uk-icon="refresh"></span></a>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="#"><span uk-icon="info"></span></a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="about_app.html"><span class="uk-padding-none">About this app</span></a>
                                </li>
                                <!--
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="about_theme.html"><span class="uk-padding-none">About this theme</span></a>
                                </li>
                                -->
                                <li class="uk-nav-divider"></li>
                                <li class="uk-link-toggle">
                                    <a class="uk-link-heading" href="about_kb4it.html"><span class="uk-padding-none">About KB4IT</span></a>
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
