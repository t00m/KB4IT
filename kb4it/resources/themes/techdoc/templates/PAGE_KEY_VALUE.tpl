= ${var['title']}

++++
        <!-- PAGE_KEY_VALUE.tpl :: START -->
<div class ="uk-container uk-overflow-auto">
    <table id="kb4it-datatable" class="uk-table uk-table-small uk-table-hover uk-table-striped" style="width:100%">
        <thead>
            <tr class="">
                <th><span class="uk-text-bold uk-text-primary">Document</span></th>
                <th><span class="uk-text-bold uk-text-primary">Team</span></th>
                <th><span class="uk-text-bold uk-text-primary">Updated</span></th>
                <th><span class="uk-text-bold uk-text-primary">Author</span></th>
                <th><span class="uk-text-bold uk-text-primary">Category</span></th>
                <th><span class="uk-text-bold uk-text-primary">Scope</span></th>
            </tr>
        </thead>
        <tbody>
            % for item in var['doclist']:
                <%
                    from kb4it.core.util import get_human_datetime, fuzzy_date_from_timestamp
                    def get_key_value(var, item, key):
                        try:
                            return var['kbdict']['document'][item][key]
                        except:
                            return ''
                            
                    title = var['kbdict']['document'][item]['Title'][0]
                    team = ', '.join(get_key_value(var, item, 'Team'))                    
                    title_url = item.replace('.adoc', '.html')
                    try:
                        published = var['kbdict']['document'][item]['Published'][0][0:10]
                    except:
                        published = ''
                    author = ', '.join(get_key_value(var, item, 'Author'))    
                    category = ', '.join(get_key_value(var, item, 'Category'))    
                    scope = ', '.join(get_key_value(var, item, 'Scope'))    
                %>
                <tr class="">
                    <td><a class="uk-link-toggle" href="${title_url}"><span class="uk-text-small uk-text-truncate">${title}</span></a></td>
                    <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${team}</span></a></td>
                    <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${published}</span></a></td>
                    <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${author}</span></a></td>
                    <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${category}</span></a></td>
                    <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${scope}</span></a></td>
                </tr>
            % endfor
        </tbody>
        <tfoot>
        </tfoot>
    </table>
</div>
        <!-- PAGE_KEY_VALUE.tpl :: END -->
++++
