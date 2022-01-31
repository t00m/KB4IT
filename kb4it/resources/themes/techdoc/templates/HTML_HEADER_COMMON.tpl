<!DOCTYPE Html>
<html lang="en">
<head>
    <title>KB4IT - ${var['title']}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="Asciidoctor 2.0.10">
    <meta name="description" content="KB4IT document">
    <meta name="author" content="KB4IT by t00mlabs.net">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="${var['theme']['path']}/framework/uikit/css/uikit.min.css" />
    <link rel="stylesheet" href="${var['theme']['path']}/framework/uikit/css/coderay-asciidoctor.css" />
    <link rel="stylesheet" href="${var['theme']['path']}/framework/uikit/css/print.css" type="text/css" media="print" />
    <link rel="stylesheet" href="${var['theme']['path']}/framework/uikit/css/kb4it.css" />
    <script src="${var['theme']['path']}/framework/uikit/js/uikit.min.js"></script>
    <script src="${var['theme']['path']}/framework/uikit/js/uikit-icons.min.js"></script>
    <script src="${var['theme']['path']}/framework/datatables/js/jquery-3.5.1.js"></script>
    <script src="${var['theme']['path']}/framework/datatables/js/jquery.dataTables.min.js"></script>
    <script src="${var['theme']['path']}/framework/datatables/js/dataTables.uikit.min.js"></script>
    <script type="text/javascript" class="init">
        $(document).ready(function() {
            $('#kb4it-datatable').DataTable( {
                dom: 'BPQrftp',
                serverSide: false,
                ordering: true,
                searching: true,
                //~ data:           data,
                deferRender:    true,
                scrollY:        500,
                scrollCollapse: false,
                scroller:       false,
                stateSave: false,
                paging:   true,
                info:     true
            } );
        } );
    </script>
</head>
<body>
<div>
<div id="container-1" class="uk-container uk-container-center">
    <div id="kb4it-menu" style="z-index: 980;" uk-sticky="show-on-up: true">
        <nav class="uk-navbar-container uk-border-rounded uk-card-hover uk-margin uk-box-shadow-large" style="background-color: white;" uk-navbar>
            <div class="uk-navbar-left noprint">
                <ul class="uk-navbar-nav">
                    <li class="uk-link-toggle">
                        <a class="uk-logo uk-card uk-card-hover" href="index.html">
                            <img src="resources/themes/${var['theme']['id']}/images/logo.png" alt="">
                        </a>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="#">Go To</a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="properties.html"><span class="uk-padding-small">Properties</span></a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-card uk-card-hover uk-border-rounded uk-link-heading" href="stats.html"><span class="uk-padding-small">Stats</span></a>
                                </li>
                            </ul>
                        </div>
                    </li>
                </ul>
                <ul class="uk-navbar-nav">
                    <!-- MENU CONTENTS :: START -->
${var['menu_contents']}
                    <!-- MENU CONTENTS :: END -->
                </ul>
            </div>
            <div class="uk-navbar-center">
                <!-- DOCUMENT TITLE :: START -->
                <ul class="uk-navbar-nav">
                    <li>
                        % if var['has_toc']:
                            ${var['actions']}
                        % endif
<!--
                       <a href="#"><span class="uk-text-bolder uk-text-truncate uk-invisible">${var['title']}</span></a>
-->
                    </li>
                </u>
                <!-- DOCUMENT TITLE :: END -->
            </div>

            <div class="uk-navbar-right noprint">
                <ul class="uk-navbar-nav">
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="#">About</a>
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