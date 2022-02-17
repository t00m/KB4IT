== All documents

++++
<div class ="uk-container uk-overflow-auto">
    <table id="kb4it-datatable" class="uk-table uk-table-small uk-table-hover uk-table-striped" style="width:100%">
        <thead>
            <tr>
                <th><span class="uk-text-bold">Document</span></th>
                <th>Title</th>
            </tr>
        </thead>
        <tbody>
            % for item in var['kbdict']['document']:
                <%
                    title = var['kbdict']['document'][item]['Title'][0]
                    title_url = item.replace('.adoc', '.html')
                %>
                <tr>
                    <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${item}</span></a></td>
                    <td><a class="uk-link-toggle" href="${title_url}"><span class="uk-text-small uk-text-truncate">${title}</span></a></td>
                </tr>
            % endfor
        </tbody>
        <tfoot>
            <tr>
                <th><span class="uk-text-bold">Document</span></th>
                <th>Title</th>
            </tr>
        </tfoot>
    </table>
</div>
++++
