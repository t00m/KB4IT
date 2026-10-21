<%
    m = var['meta']
%><!-- kb4it:meta -->
% if m['description'] and not m['has_description']:
<meta name="description" content="${m['description']}">
% endif
% if m['author'] and not m['has_author']:
<meta name="author" content="${m['author']}">
% endif
% if m['url']:
<link rel="canonical" href="${m['url']}">
<meta property="og:url" content="${m['url']}">
% endif
<meta property="og:title" content="${m['title']}">
<meta property="og:type" content="${m['type']}">
<meta property="og:site_name" content="${m['site_name']}">
% if m['description']:
<meta property="og:description" content="${m['description']}">
% endif
% if m['image']:
<meta property="og:image" content="${m['image']}">
<meta name="twitter:card" content="summary_large_image">
% else:
<meta name="twitter:card" content="summary">
% endif
% if m['feed']:
<link rel="alternate" type="application/atom+xml" title="${m['site_name']}" href="${m['feed']}">
% endif
% if m['favicon']:
<link rel="icon" href="${m['favicon']}">
% endif
% if m['math']:
<link rel="stylesheet" href="resources/render/katex/katex.min.css">
<script defer src="resources/render/katex/katex.min.js"></script>
% endif
% if m['mermaid']:
<script defer src="resources/render/mermaid/mermaid.min.js"></script>
% endif
% if m['math'] or m['mermaid']:
<script defer src="resources/render/kb4it-render.js"></script>
% endif
<!-- /kb4it:meta -->
