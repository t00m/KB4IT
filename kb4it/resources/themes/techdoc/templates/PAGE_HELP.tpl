= Help

:SystemPage:    Yes

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

== KB4IT Documents

Any KB4IT document is made of two sections:

. Header
. Body

=== Header

By using a first level section (`=`) you set the *title of the document*.

Then, enclosed by (`:`) you set its *properties*.

Examples of properties: Author, Category, Scope, Status, Priority, Team, Periodicity, etc...

Finally, you must indicate the end of the header with this line:

`// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE`

.*Example of header of a KB4IT document*
----
= How to write asciidoc documents for KB4IT

:Author:        John Doe
:Category:      Help
:Scope:         Technical documentation
:Status:        Released
:Priority:      Normal
:Team:          IT Plumbers

// Extra properties
:Periodicity:   Timely

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

----

=== Body

After you write the header, you can start writing your document.

The body *must* use Asciidoc format.

It is recommended to split your document in logic sections in order to make it more readable:

----
== Section 1

=== Section 1.1

=== Section 1.2

== Section 2

=== Section 2.1
----

:TIP: Use the source code of other KB4IT pages as templates or write your own page from the scratch.

== References

Take a look to the https://docs.asciidoctor.org/asciidoc/latest/syntax-quick-reference/[AsciiDoc Syntax Quick Reference] for a quick start or read the https://asciidoctor.org/docs/asciidoc-writers-guide/[AsciiDoc Writer’s Guide] for a deeper understanding of Asciidoc markdown format.

