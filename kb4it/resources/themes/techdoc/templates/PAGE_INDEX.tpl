= ${var['page']['title']}

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

% if var['repo']['webserver'] == 'true':
++++
<div id="timeline-embed" style="width: 100%; height: 600px;"></div>

<script src="resources/themes/techdoc/framework/TimelineJS/js/timeline.js"></script>
<script>
    var timeline = new TL.Timeline('timeline-embed', 'timeline_main.json');
</script>
++++

% else:

++++
<div class ="uk-container uk-overflow-auto">
${var['page']['dt_documents']}
</div>
++++

% endif
