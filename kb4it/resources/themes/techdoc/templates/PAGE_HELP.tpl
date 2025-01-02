= Help

:SystemPage:    Yes

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

== Introduction

_KB4IT_ is a static website generator based on Asciidoctor sources mainly for technical documentation purposes.

Given a set of source documents, KB4IT builds a website based on a specific theme.

The Default theme for KB4IT is _techdoc_.

== Motivations

* The main aim is to provide an easy way to write my technical documentation.
* Don't care about the formatting and focus on the contents.
* To allow teams to manage their knowledge database easily.
* Do not depend on third software products like word processors or
complex web applications.


== Features

=== Pros

* Writing documentation: Documents must be in Asciidoctor format which is easy to learn.
* Finding documents: Once a document is converted to html, properties can be browsed. Moreover, property pages have filters and a search entry to filter by title.
* Publishing your repository: all necessary files are inside a directory. Browse it or copy it to your web server.
* Serverless: There is no need for a web server. Of course, you can use one if you please.
* Smart compiling: Only those documents added or modified are compiled.
* Use the default themes or build your own custom theme
* By modifying templates, it might be integrated with Github or Gitlab.

=== Cons

* Not to much documentation at this moment
* No online editor: At this moment, KB4IT doesn't include any online editor. You must create or edit your documents with your preferred editor.
* No dynamic search: KB4IT was developed to be as simple as possible.
* No dependencies at all excepting Asciidoctor (as text processor and publishing toolchain) and Python (the programming language used).
* API is not stable
* Most of the requirements are tailored to my own necessities which might not be the same as yours.


== KB4IT Documents

Taking as an example this page, a KB4IT document is made of two main parts:

. Header
. Body

=== Header

By using a first level section (`=`) you set the *title of the document*.

Then, enclosed by (`:`) you set its *properties*.

There are *six core properties* (Author, Category, Scope, Status, Priority and Team).

Moreover, you can add any property you imagine. There is no limits.

Finally, you must indicate the end of the header with this line:

`// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE`

.*Source*
----
= How to write asciidoc documents for KB4IT
:Author:        John Doe
:Category:      Help
:Scope:         Technical documentation
:Status:        Released
:Priority:      Normal
:Team:          IT Plumbers

// Extra properties
:Periodicity:   Daily

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

----

=== Body

After you write the header, you can start writing your document.

:TIP: Use the source code of other KB4IT pages as templates or write your own page from the scratch.
