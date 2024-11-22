= ${var['page']['title']}

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

% if var['repo']['webserver']:
++++
<div id="timeline-embed" style="width: 100%; height: 600px;"></div>

<script src="resources/themes/techdoc/framework/TimelineJS/js/timeline.js"></script>
<script>
    var options = {
            start_at_end: true,
	    initial_zoom: "2"
        }
    var timeline = new TL.Timeline('timeline-embed', 'timeline_main.json', options);
</script>
++++

% else:

++++
<div class ="uk-container uk-overflow-auto">
${var['page']['dt_documents']}
</div>
++++

% endif
