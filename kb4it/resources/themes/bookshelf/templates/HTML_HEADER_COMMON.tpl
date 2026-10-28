<%!
from kb4it.core.util import valid_filename
%>
<!DOCTYPE html>
<html lang="${var['lang']}">
<head>
    <!-- PAGE METADATA :: START -->
    <meta charset="UTF-8">
    <title>${var['repo']['title']} - ${var['page']['title']}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="generator" content="KB4IT ${var['env']['APP']['build_version']}; ${var['theme'].get('identity', '')}">
    <!-- PAGE METADATA :: END -->
    <!-- STYLESHEETS :: START -->
    <link rel="stylesheet" href="resources/themes/bookshelf/framework/bookshelf/css/theme.css">
% if (var['repo'].get('markdown') or {}).get('highlight', 'client') == 'pygments':
    <link rel="stylesheet" href="resources/pygments.css">
% endif
    <link rel="stylesheet" href="resources/themes/bookshelf/framework/bookshelf/css/print.css" media="print">
    <!-- STYLESHEETS :: END -->
</head>
<body>
<!-- PAGE :: START -->
<% cb = var['bk'].get('current_book') %>
<!-- TOP BAR :: START -->
<header class="app-top">
    <div class="app-top-inner">
        <!-- SITE NAME :: START -->
        <a class="brand" href="index.html">
            <span class="mark">KB</span>
            <span class="name">${var['repo']['title']}</span>
        </a>
        <!-- SITE NAME :: END -->
% if cb:
        <!-- CURRENT BOOK :: START -->
        <a class="book-switch" href="${cb['url']}" title="${cb['title']}">
            <span class="dot ${cb['bucket']}"></span>
            <span>${cb['short']}</span>
            <span class="caret">&#9662;</span>
        </a>
        <!-- CURRENT BOOK :: END -->
% endif
% if var.get('search_box'):
        <!-- SEARCH BOX :: START -->
        <div class="search">${var['search_box'] | n}</div>
        <!-- SEARCH BOX :: END -->
% else:
        <!-- BROWSE LINK :: START -->
        <a class="search" href="all.html">
            <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="9" cy="9" r="6"></circle><path d="M14 14l4 4"></path></svg>
            <span>Browse chapters, commands, tags&hellip;</span>
            <span class="kbd">All</span>
        </a>
        <!-- BROWSE LINK :: END -->
% endif
        <!-- TOP ACTIONS :: START -->
        <div class="top-actions">
% if var['editor']:
            <a class="icon-btn" href="add.html" title="Add document"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10 4v12"></path><path d="M4 10h12"></path></svg></a>
% endif
            <a class="icon-btn" href="properties.html" title="Properties"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><ellipse cx="10" cy="5" rx="7" ry="2.6"></ellipse><path d="M3 5v10c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6V5"></path><path d="M3 10c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6"></path></svg></a>
            <a class="icon-btn" href="${var['help_url']}" target="_blank" rel="noopener" title="Help"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="10" cy="10" r="8"></circle><path d="M10 9v5"></path><circle cx="10" cy="6.2" r="0.6" fill="currentColor"></circle></svg></a>
        </div>
        <!-- TOP ACTIONS :: END -->
    </div>
</header>
<!-- TOP BAR :: END -->
