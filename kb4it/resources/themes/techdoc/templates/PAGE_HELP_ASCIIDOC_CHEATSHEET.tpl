= Asciidoc Cheatsheet

:SystemPage:    Yes

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE


[[Cheatsheet]]
== Asciidoc Cheatsheet

Check <<references,Asciidoc references>> for an extended documentation.

=== Paragraphs

[source, adoc]
.*Source*
----
A normal paragraph.
Line breaks are not preserved.
// line comments, which are lines that start with //, are skipped

A blank line separates paragraphs.

 An indented (literal) paragraph disables text formatting,
 preserves spaces and line breaks, and is displayed in a
 monospaced font.
----

*Output*

A normal paragraph.
Line breaks are not preserved.
// line comments, which are lines that start with //, are skipped

A blank line separates paragraphs.

 An indented (literal) paragraph disables text formatting,
 preserves spaces and line breaks, and is displayed in a
 monospaced font.


=== Text Formatting

[source, adoc]
.*Source*
----
*strong importance* (aka bold)
_stress emphasis_ (aka italic)
`monospaced` (aka typewriter text)
----

*Output*

_stress emphasis_ (aka italic)

*strong importance* (aka bold)

`monospaced` (aka typewriter text)


=== Admonitions

.*Source*
----
NOTE: This is a note
TIP: This is a tip
IMPORTANT: This is important
CAUTION: This is a caution message
WARNING: This is a warning
----

*Output*

NOTE: This is a note

TIP: This is a tip

IMPORTANT: This is important

CAUTION: This is a caution message

WARNING: This is a warning


=== Links

[source, adoc]
.*Source*
----
https://example.org/page[A webpage]
link:../path/to/file.txt[A local file]
xref:document.adoc[A sibling document]
mailto:hello@example.org[Email to say hello!]
----

*Output*

https://example.org/page[A webpage]

link:../path/to/file.txt[A local file]

xref:document.adoc[A sibling document]

mailto:hello@example.org[Email to say hello!]


=== Anchors

[source, adoc]
.*Source*
----
[[id-name, reference text]]
// or written using normal block attributes as `[#id-name,reftext=reference text]`
A paragraph (or any block) with an anchor (aka ID) and reftext.

See <<idname>> or <<idname,optional text of internal link>>.

xref:document.adoc#idname[Jumps to anchor in another document].

This paragraph has a footnote.footnote:[This is the text of the footnote.]
----

*Output*

[[id-name,reference text]]
// or written using normal block attributes as `[#idname,reftext=reference text]`
A paragraph (or any block) with an anchor (aka ID) and reftext.

See <<idname>> or <<idname,optional text of internal link>>.

xref:document.adoc#idname[Jumps to anchor in another document].

This paragraph has a footnote.footnote:[This is the text of the footnote.]



=== Lists

[source, adoc]
.*Source*
----
*Unordered*

* level 1
** level 2
*** level 3
**** level 4
***** etc.
* back at level 1
+
Attach a block or paragraph to a list item using a list continuation (which you can enclose in an open block).

.Some Authors
[circle]
- Edgar Allen Poe
- Sheri S. Tepper
- Bill Bryson

*Ordered*

. Step 1
. Step 2
.. Step 2a
.. Step 2b
. Step 3

.Remember your Roman numerals?
[upperroman]
. is one
. is two
. is three

*Checklist*

* [x] checked
* [ ] not checked


*Callout*

// enable callout bubbles by adding `:icons: font` to the document header
[,ruby]
 puts 'Hello, World!' # <1>
<1> Prints `Hello, World!` to the console.

*Descriptions*

first term:: description of first term

second term::

description of second term
----

*Output*

*Unordered*

* level 1
** level 2
*** level 3
**** level 4
***** etc.
* back at level 1
+
Attach a block or paragraph to a list item using a list continuation (which you can enclose in an open block).

.Some Authors
[circle]
- Edgar Allen Poe
- Sheri S. Tepper
- Bill Bryson

*Ordered*

. Step 1
. Step 2
.. Step 2a
.. Step 2b
. Step 3

.Remember your Roman numerals?
[upperroman]
. is one
. is two
. is three

*Checklist*

* [x] checked
* [ ] not checked

*Callouts*

// enable callout bubbles by adding `:icons: font` to the document header
[,ruby]
----
puts 'Hello, World!' # <1>
----
<1> Prints `Hello, World!` to the console.

*Descriptions*

first term:: description of first term
second term::
description of second term


=== Sections

[source, adoc]
.*Source*
----
= Document Title (Level 0)
== Level 1
=== Level 2
==== Level 3
===== Level 4
====== Level 5
== Back at Level 1
----

*Output*

==== Level 3
===== Level 4
==== Back at Level 3


=== Tables

[source, adoc]
.*Source*
----
[options="header", width="100%", cols="10%,70%,10%,10%"]
|===
| Active
| Server
| User
| Pass

| No
| `Server1`
| `.\adminuser`
| `adminpass.345`

| Yes
| `Server2`
| `.\adminuser`
| `passadmin.543`
|===

----

*Output*

[options="header", width="100%", cols="10%,70%,10%,10%"]
|===
| Active
| Server
| User
| Pass

| No
| `Server1`
| `.\adminuser`
| `adminpass.345`

| Yes
| `Server2`
| `.\adminuser`
| `passadmin.543`
|===


=== Multimedia

[source, adoc]
.*Source*
----
image::resources/images/logo.png[]
----

*Output*

image::resources/images/logo.png[]


[[References]]
== References

* https://asciidoctor.org/docs/asciidoc-writers-guide/[AsciiDoc Writer’s Guide]
* https://powerman.name/doc/asciidoc[AsciiDoc cheatsheet]
* https://asciidoctor.org/docs/what-is-asciidoc/[What is AsciiDoc? Why do we need it?]
