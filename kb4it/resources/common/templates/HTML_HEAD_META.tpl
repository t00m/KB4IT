<%
    m = var['meta']
%><!-- kb4it:meta -->
% if m['description'] and not m['has_description']:
<meta name="description" content="${m['description'] | h}">
% endif
% if m['author'] and not m['has_author']:
<meta name="author" content="${m['author'] | h}">
% endif
% if m['url']:
<link rel="canonical" href="${m['url'] | h}">
<meta property="og:url" content="${m['url'] | h}">
% endif
<meta property="og:title" content="${m['title'] | h}">
<meta property="og:type" content="${m['type']}">
<meta property="og:site_name" content="${m['site_name'] | h}">
% if m['description']:
<meta property="og:description" content="${m['description'] | h}">
% endif
% if m['image']:
<meta property="og:image" content="${m['image'] | h}">
<meta name="twitter:card" content="summary_large_image">
% else:
<meta name="twitter:card" content="summary">
% endif
% if m['feed']:
<link rel="alternate" type="application/atom+xml" title="${m['site_name'] | h}" href="${m['feed']}">
% endif
<!-- /kb4it:meta -->
