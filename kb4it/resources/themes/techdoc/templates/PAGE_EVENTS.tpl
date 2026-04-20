= Events

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

++++
<div class="uk-container uk-margin-top">

  <ul class="uk-tab" id="kb4it-events-tabs"
      uk-tab="connect: #kb4it-events-switcher; animation: uk-animation-fade">
    % for ydata in var['years']:
    <li><a href="#">${ydata['year']} <span class="uk-badge">${ydata['count']}</span></a></li>
    % endfor
  </ul>

  <ul id="kb4it-events-switcher" class="uk-switcher uk-margin">
    % for ydata in var['years']:
    <li>
      <div class="uk-margin-bottom">
        ${ydata['calendar']}
      </div>
      <div class="uk-overflow-auto">
        ${ydata['datatable']}
      </div>
    </li>
    % endfor
  </ul>

</div>

<script>
(function () {
  % for ydata in var['years']:
  (function () {
    var tid = 'kb4it-datatable-${ydata["year"]}';
    var el = document.getElementById(tid);
    if (el && !$.fn.DataTable.isDataTable('#' + tid)) {
      $('#' + tid).attr('data-dt-init', '1').DataTable({
        dom: '<"kbfilter"flrtip>',
        serverSide: false,
        ordering: true,
        searching: true,
        deferRender: true,
        autoWidth: false,
        stateSave: false,
        paging: false,
        info: true,
        order: [[0, 'desc']]
      });
    }
  })();
  % endfor

  UIkit.util.on('#kb4it-events-switcher', 'shown', function (e) {
    $(e.target).find('.kb4it-datatable').each(function () {
      if ($.fn.DataTable.isDataTable(this)) {
        $(this).DataTable().columns.adjust();
      }
    });
  });
})();
</script>
++++
