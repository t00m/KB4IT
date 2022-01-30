<!-- Template SECTION_RELATED.tpl :: START -->
% if var['has_docs']:
    <table id="kb4it-datatable" class="uk-table uk-table-divider uk-table-striped uk-table-hover uk-table-small uk-card uk-card-hover">
    <thead>
        <tr>
            <th><span class="uk-text-bold">Tag</span></th>
            <th><span class="uk-text-bold">Document</span></th>
        </tr>
    </thead>
    <tbody>
    % for tag in var['related']:        
            <tr>
                <td class="10%">
                    <a class="uk-link-text" href="Tag_${tag}.html">
                        <div class="uk-text-bolder uk-text-secondary uk-text-bold uk-text-meta">${tag}</div>
                    </a>
                </td>
                <td width="90%">
                    <%
                        llinks = []
                    %> 
                    % for doc in var['related'][tag]:
                        <% 
                            title = var['srvdtb'].get_values(doc, 'Title')[0]
                            href = doc.replace('.adoc', '.html')
                            link = """<a class="uk-link-text" href="%s">%s</a>""" % (href, title)
                            llinks.append(link)
                        %>                        
                    % endfor                    
                    <%
                        links = ', '.join(llinks)
                    %>
                    <div class="uk-text-meta">${links}</div>
                </td>
            </tr>        
    % endfor
    </tbody>
    <tfoot>
    </tfoot>
    </table>
% else:
    <div class="uk-alert-danger" uk-alert><p>No documents found.</p></div>
% endif
<!-- Template SECTION_RELATED.tpl :: END -->
