<!DOCTYPE html>
<html lang="${var['lang']}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${var['page']['title']} | ${var['repo']['title']}</title>
    <link rel="stylesheet" href="resources/vendor/uikit/css/uikit.min.css">
    <script src="resources/vendor/uikit/js/uikit.min.js"></script>
    <script src="resources/vendor/uikit/js/uikit-icons.min.js"></script>
</head>
<body>
<nav class="uk-navbar-container uk-padding-small" data-uk-navbar>
    <div class="uk-navbar-left">
        <a class="uk-navbar-item uk-logo" href="index.html">${var['repo']['title']}</a>
        <ul class="uk-navbar-nav">
            <li><a href="all.html">All documents</a></li>
            <li><a href="properties.html">Properties</a></li>
        </ul>
    </div>
    <div class="uk-navbar-right">${var['search_box'] | n}</div>
</nav>
<div class="uk-container uk-margin">
