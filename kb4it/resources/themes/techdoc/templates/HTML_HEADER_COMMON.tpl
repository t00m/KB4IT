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
    <link rel="stylesheet" href="resources/common/uikit/css/uikit.min.css">
    <link rel="stylesheet" href="resources/common/uikit/css/coderay-asciidoctor.css">
    <link rel="stylesheet" href="resources/common/uikit/css/print.css" type="text/css" media="print" />
    <link rel="stylesheet" href="resources/common/uikit/css/kb4it.css">
    <script src="resources/common/uikit/js/uikit.min.js"></script>
    <script src="resources/common/uikit/js/uikit-icons.min.js"></script>
</head>
<body>
<div id="container-1" class="uk-container">
    <div class="" id="kb4it-menu" uk-sticky="show-on-up: true">
        <nav class="uk-navbar-container uk-border-rounded uk-card-hover" style="background-color: white;" uk-navbar>
            <div class="uk-navbar-left noprint">
                <ul class="uk-navbar-nav">
                    <li class="uk-link-toggle">
                        <a class="uk-logo uk-card uk-card-hover" href="index.html">
                            <img src="resources/themes/${var['theme']['id']}/images/logo.png" alt="">
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
                            </ul>
                        </div>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-link-heading" href="https://github.com/user/repository/new/master" target="_blank"><span uk-icon="plus"></span></a>
                    </li>
                    <li class="uk-nav-divider"></li>
                </ul>
                <ul class="uk-navbar-nav">
                    <!-- MENU CONTENTS :: START -->
${var['menu_contents']}
                    <!-- MENU CONTENTS :: END -->
                </ul>
            </div>
