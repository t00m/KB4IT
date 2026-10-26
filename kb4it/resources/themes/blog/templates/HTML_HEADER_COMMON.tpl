<% _hl = (var['repo'].get('markdown') or {}).get('highlight', 'client') %>
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- PAGE METADATA :: START -->
  <meta charset="UTF-8">
  <title>${var['repo']['title']} - ${var['page']['title']}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="KB4IT ${var['env']['APP']['build_version']}; ${var['theme'].get('identity', '')}">
  <!-- PAGE METADATA :: END -->
  <!-- STYLESHEETS :: START -->
% if _hl == 'client':
  <link rel="stylesheet" href="resources/themes/blog/framework/Highlight/styles/github-dark.css">
% elif _hl == 'pygments':
  <link rel="stylesheet" href="resources/pygments.css">
% endif
  <link rel="stylesheet" href="resources/themes/blog/css/blog.css">
  <link rel="stylesheet" href="resources/themes/blog/framework/uikit/css/uikit.min.css">
  <!-- STYLESHEETS :: END -->
  <!-- LIBRARIES :: START -->
% if _hl == 'client':
  <script src="resources/themes/blog/framework/Highlight/highlight.js"></script>
% endif
  <script src="resources/themes/blog/framework/uikit/js/uikit.min.js"></script>
  <script src="resources/themes/blog/framework/uikit/js/uikit-icons.min.js"></script>
  <script src="resources/themes/blog/framework/datatables/js/jquery-3.5.1.js"></script>
  <script src="resources/themes/blog/framework/datatables/js/jquery.dataTables.min.js"></script>
  <script src="resources/themes/blog/framework/datatables/js/dataTables.uikit.min.js"></script>
  <!-- LIBRARIES :: END -->
  <!-- DATATABLES SETUP :: START -->
  <script class="init">
        $(document).ready(function() {
            $('#kb4it-datatable').DataTable( {
                dom: '<"kbfilter"Bifrt>',
                serverSide: false,
                pageLength: 1000,
                ordering: true,
                searching: true,
                //~ data:           data,
                deferRender:    true,
                scrollY: 600,
                scrollCollapse: true,
                scroller:       true,
                stateSave: false,
                paging:   true,
                info:     true,
                order: [[ 0, "desc" ]]
            } );
        } );
  </script>
  <!-- DATATABLES SETUP :: END -->
</head>
<body>
<!-- PAGE :: START -->
<div class="blog-container uk-container" data-uk-height-viewport="expand: true">
    <div class="uk-grid">
        <!-- CONTENT COLUMN :: START -->
        <div class="uk-width-3-4@m">
