<!DOCTYPE Html>
<html lang="en">
<head>
    <title>KB4IT - %s</title>
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
<div>
<div id="container-1" class="uk-container uk-container-center">
    <div id="kb4it-menu" style="z-index: 980;" uk-sticky="show-on-up: true">
        <nav class="uk-navbar-container uk-border-rounded uk-card-hover uk-margin" style="background-color: white;" uk-navbar>
            <div class="uk-navbar-left noprint">
                <ul class="uk-navbar-nav">
                    <li class="uk-link-toggle">
                        <a class="uk-logo uk-card uk-card-hover" href="index.html">
                            <img src="resources/images/logo.png" alt="">
                        </a>
                    </li>
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="#">Go To</a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li class="uk-link-toggle">
                                    <a class="uk-button uk-card uk-card-hover uk-link-heading" href="properties.html">Properties</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="recents.html">Recents</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="bookmarks.html">Bookmarks</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="events.html">Events</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="blog.html">Blog</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="stats.html">Stats</a>
                                </li>
                            </ul>
                        </div>
                    </li>
                </ul>
                <ul class="uk-navbar-nav">
                    <!-- MENU CONTENTS :: START -->
%s
                    <!-- MENU CONTENTS :: END -->
                </ul>
            </div>
            <div class="uk-navbar-center">
                <!-- DOCUMENT TITLE :: START -->
                <ul class="uk-navbar-nav">
                    <li>
                       <a href="#"><span class="uk-text-emphasis uk-text-truncate">%s</span></a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li>
                                    <!-- View Metadata Button :: START -->
                                    <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="#modal-full-metadata" uk-toggle><span class="">Metadata</span></a>
                                    <div id="modal-full-metadata" class="uk-modal-full" uk-modal>
                                        <div class="uk-modal-dialog">
                                            <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                                            <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                                                <div class="uk-padding-large uk-background-muted">
                                                    <div class="uk-text-lead uk-text-center uk-text-danger">Metadata</div>
<!-- METADATA :: START -->
%s
<!-- METADATA :: END -->
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <!-- View Metadata Button :: END -->
                                </li>
                                <li>
                                    <!-- View Asciidoc Source Button :: START -->
                                    <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="#modal-full-source" uk-toggle><span class="">Source</span></a>
                                    <div id="modal-full-source" class="uk-modal-full" uk-modal>
                                        <div class="uk-modal-dialog">
                                            <button class="uk-modal-close-full uk-close-large uk-background-muted" type="button" uk-close></button>
                                            <div class="uk-grid-collapse uk-child-width-expand@s uk-flex-middle" uk-grid>
                                                <div class="uk-padding-large uk-background-muted">
                                                    <div class="uk-text-lead uk-text-center uk-text-danger">Source</div>
                                                    <div class="uk-text-lead">%s&nbsp;<a onclick="copyToClipboard()" class="uk-icon-link uk-margin-small-right" uk-icon="copy"></a></div>
                                                    <textarea id="source-code" class="uk-width-1-1 uk-height-viewport">%s</textarea>
                                                </div>
                                            </div>
                                        </div>
                                    </div> <!-- View Source Button :: END -->
                                </li>
                            </ul>
                        </div>
                    </li>
                </u>
                <!-- DOCUMENT TITLE :: END -->
            </div>
            <div class="uk-navbar-right noprint">
                <ul class="uk-navbar-nav">
                    <li>
                        <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="#">Help</a>
                        <div class="uk-navbar-dropdown">
                            <ul class="uk-nav uk-navbar-dropdown-nav">
                                <li class="uk-link-toggle">
                                    <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="help.html">Help</a>
                                </li>
                                <li class="uk-link-toggle">
                                    <a class="uk-button uk-card uk-card-hover uk-button uk-card uk-card-hover uk-link-heading" href="about.html">About</a>
                                </li>
                                <!--
                                <li class="uk-link-toggle">
                                    <a class="uk-button uk-card uk-card-hover uk-link-heading" href="rss.xml"><span class="uk-margin-small-right" uk-icon="icon: rss"></span></a>
                                </li>
                                -->
                            </ul>
                        </div>
                    </li>
                </ul>
            </div>
        </nav>
    </div>
</div>
<div class="uk-container uk-container-center">
