<%!
from kb4it.core.util import valid_filename
%>
<!DOCTYPE html>
<html lang="en">
<head>
    <title>${var['repo']['title']} - ${var['page']['title']}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="KB4IT ${var['env']['APP']['version']}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@500;700;900&family=Red+Hat+Text:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="resources/themes/bookshelf/framework/bookshelf/css/theme.css">
% if (var['repo'].get('markdown') or {}).get('highlight', 'client') == 'pygments':
    <link rel="stylesheet" href="resources/pygments.css">
% endif
    <link rel="stylesheet" href="resources/themes/bookshelf/framework/bookshelf/css/print.css" media="print">
</head>
<body>
<% cb = var['bk'].get('current_book') %>
<header class="app-top">
    <div class="app-top-inner">
        <a class="brand" href="index.html">
            <span class="mark">KB</span>
            <span class="name">${var['repo']['title']}</span>
        </a>
% if cb:
        <a class="book-switch" href="${cb['url']}" title="${cb['title']}">
            <span class="dot ${cb['bucket']}"></span>
            <span>${cb['short']}</span>
            <span class="caret">&#9662;</span>
        </a>
% endif
% if var.get('search_box'):
        <div class="search">${var['search_box'] | n}</div>
% else:
        <a class="search" href="all.html">
            <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="9" cy="9" r="6"></circle><path d="M14 14l4 4"></path></svg>
            <span>Browse chapters, commands, tags&hellip;</span>
            <span class="kbd">All</span>
        </a>
% endif
        <div class="top-actions">
% if var['editor']:
            <a class="icon-btn" href="add.html" title="Add document"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10 4v12"></path><path d="M4 10h12"></path></svg></a>
% endif
            <a class="icon-btn" href="properties.html" title="Properties"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><ellipse cx="10" cy="5" rx="7" ry="2.6"></ellipse><path d="M3 5v10c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6V5"></path><path d="M3 10c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6"></path></svg></a>
            <a class="icon-btn" href="help.html" title="Help"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="10" cy="10" r="8"></circle><path d="M10 9v5"></path><circle cx="10" cy="6.2" r="0.6" fill="currentColor"></circle></svg></a>
        </div>
    </div>
</header>
