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
    <link rel="stylesheet" href="resources/themes/blog/framework/uikit/css/uikit.min.css" />
    <link rel="stylesheet" href="resources/themes/blog/framework/kb4it/css/coderay-asciidoctor.css" />
    <link rel="stylesheet" href="resources/themes/blog/framework/kb4it/css/print.css" type="text/css" media="print" />
    <link rel="stylesheet" href="resources/themes/blog/framework/kb4it/css/screen.css" />
    <link rel="stylesheet" href="resources/themes/blog/framework/TimelineJS/css/timeline.css" />
    <script src="resources/themes/blog/framework/uikit/js/uikit.min.js"></script>
    <script src="resources/themes/blog/framework/uikit/js/uikit-icons.min.js"></script>
    <script src="resources/themes/blog/framework/datatables/js/jquery-3.5.1.js"></script>
    <script src="resources/themes/blog/framework/datatables/js/jquery.dataTables.min.js"></script>
    <script src="resources/themes/blog/framework/datatables/js/dataTables.uikit.min.js"></script>
    <script type="text/javascript" class="init">
        $(document).ready(function() {
            $('#kb4it-datatable').DataTable( {
                dom: '<"kbfilter"flrtip>',
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
    <style>
        body {
            background-color: #f8f8f8;
            padding-top: 40px;
        }
        .blog-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .post-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .post-card:hover {
            <!-- transform: translateY(-5px); -->
        }
        .post-meta {
            color: #666;
            font-size: 0.9rem;
        }
        .post-tags {
            margin-top: 15px;
        }
        .tag {
            background-color: #f1f1f1;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8rem;
            margin-right: 5px;
        }
        .category {
            color: #1e87f0;
            font-weight: 500;
        }
        .sidebar {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 20px;
            position: sticky;
            top: 40px;
        }
        .sidebar-title {
            border-bottom: 1px solid #e5e5e5;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
