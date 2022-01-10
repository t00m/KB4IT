<div class ="uk-container">
    <table id="kb4it-datatable" class="uk-table uk-table-hover uk-table-striped" style="width:100%">
        <thead>
            <tr>
                <th><span class="uk-text-bold">Document</span></th>
                <th>Team</th>
                <th>Published</th>
                <th>Author</th>
                <th>Category</th>
                <th>Scope</th>
            </tr>
        </thead>
        <tbody>

            % for item in var['kbdict']['document']:
                <%
                    from kb4it.core.util import get_human_datetime, fuzzy_date_from_timestamp
                    title = var['kbdict']['document'][item]['Title'][0]
                    team = ', '.join(var['kbdict']['document'][item]['Team'])
                    title_url = """<a class="uk-link" href="%s">%s</a>""" % (item.replace('.adoc', '.html'), title)
                    published = fuzzy_date_from_timestamp(var['kbdict']['document'][item]['Published'][0])
                    author = ', '.join(var['kbdict']['document'][item]['Author'])
                    category = ', '.join(var['kbdict']['document'][item]['Category'])
                    scope = ', '.join(var['kbdict']['document'][item]['Scope'])
                %>
                <tr>
                    <td>${title_url}</td>
                    <td>${team}</td>
                    <td>${published}</td>
                    <td>${author}</td>
                    <td>${category}</td>
                    <td>${scope}</td>
                </tr>
            % endfor
        </tbody>
        <tfoot>
            <tr>
                <th><span class="uk-text-bold">Document</span></th>
                <th>Team</th>
                <th>Published</th>
                <th>Author</th>
                <th>Category</th>
                <th>Scope</th>
            </tr>
        </tfoot>
    </table>
</div>