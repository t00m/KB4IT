<div class="uk-container uk-margin-top">

  <div class="uk-flex uk-flex-center uk-margin">
    <select id="kb4it-events-year-select" class="uk-select uk-form-width-medium uk-text-center">
      % for i, ydata in enumerate(var['years']):
      <option value="${i}" ${'selected' if i == 0 else ''}>${ydata['year']} (${ydata['count']})</option>
      % endfor
    </select>
  </div>

  <ul id="kb4it-events-switcher" class="uk-switcher uk-margin">
    % for ydata in var['years']:
    <li>
      <div hidden></div>
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
  var switcher = UIkit.switcher('#kb4it-events-switcher');

  document.getElementById('kb4it-events-year-select').addEventListener('change', function () {
    switcher.show(parseInt(this.value));
  });

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
