= About KB4IT
:Author:        t00mlabs
:Category:      Help
:Scope:         Documentation
:Status:        Released
:Priority:      Normal
:Team:          IT Plumbers

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE


== Introduction

*KB4IT* is a static website generator based on Asciidoctor sources mainly for technical documentation purposes.

Taking advantage of the `user-defined attributes` feature in Asciidoctor, KB4IT can parse Asciidoctor sources, extract all metadata available and create something similar to a wiki. In this way, all information provided by the user can be easily related.


== Motivations:

* The main aim is to provide an easy way to write technical documentation.
* Don't care about the formatting and focus on the contents.
* To allow teams to manage their knowledge database easily.
* Do not depend on third software products like word processors or complex web applications.


== Features

[options="header", width="100%", cols="50%,50%"]
|===
| *Pros*
| *Cons*

| Easy to *write* technical documentation
| *No online editor*.

| Easy to *find* documentation
| There is *no dynamic search*. 

Search is based on static filters generated each time a page is compiled.

| Easy to *publish* documentation
|

| Easy to *backup/restore* documentation
|

| *Serverless*
|

| *Smart compiling*
|
|===

=== Pros

==== Writing documentation
Documents must be in Asciidoctor format which is easy to learn.

See <<help.adoc#, help>> page for more details.

Take into account that, for each document, there is its corresponding Asciidoctor source. So you can use it as a template to write another document without spending too much time.

==== Fiding documents
There are many ways to find the document you are looking for.

Firstly, each document has properties which can you can browse.
Eg.: If you remember the author of a document, just visit the author page.

Also, properties pages have filters. Moreover, there is a search entry to filter results by writing some of the letters of the title.

==== Publishing your repository
All documents you write are compiled/converted to HTML files.

Just put them in any folder and point your browser to `<target_path>\index.html`.

However, you can upload/copy them to your webserver.

==== Serverless

There is no need for a web server. Of course, you can use one if you please.

However, KB4IT was designed to work in mixed environments where people use shared folders (Eg.: Windows shares or directories mounted by NFS).


==== Smart compiling

Only those documents added or modified are compiled. It reduces drastically the amount of time and CPU needed to generate the website.

However, to achieve this, KB4IT uses a cache. If the cache is deleted or missing, the whole repository is compiled again.

A repository with 100 documents, in a Linux Virtual Machine with 2 CPU and 2G memory it takes less than 2 mins. Other tests carried out in a server with more CPUs and memory, the compilation time is much less.

To speed up the compilation, KB4IT uses threading. By default, it launches 30 threads in parallel. So, please, be aware of this feature, as it will eat all CPU available until the compilation finishes.

=== Cons

==== No online editor

At this moment, KB4IT doesn't include any online editor. You must create or edit your documents with your preferred editor.

==== No dynamic search

KB4IT was developed to be as simple as possible. No dependencies at all excepting Asciidoctor (as text processor and publishing toolchain) and Python (the programming language used).

The main goal was to have something like a Wiki but just with plain HTML files in a directory. Nothing else. Because of this, no full-text search can be implemented.

== How it works

=== Workflow

This is the flow:

. Get source documents
. Preprocess documents (get metadata)
. Process documents in a temporary dir
. Compile documents to HTML with Asciidoctor
. Delete contents of target directory (if any)
. Copy all resources (global and local) to the target path
. Copy all documents to the target path
. Copy source docs to the target path


=== Hacking

KB4IT is a set of Python 3 scripts.

The code is organized in the following way:

----
kb4it
├── resources
│   ├── offline
│   │   ├── docinfo
│   │   └── templates
│   └── online
│       ├── images
│       └── uikit
│           ├── css
│           ├── fonts
│           └── js
└── src
    ├── core
    └── services
----

* *Offline* resources: they are used to build target files (templates)
* *Online*: resources to be copied to target directory

== Installation

=== Command line

`python3 setup.py install --user`

=== Pypi

`sudo pip install kb4it --user`

== Execution

The most typical usage would be:

----
$HOME/.local/bin/kb4it -sp /path/to/source/docs -tp /var/www/html/repo --log INFO
----


Display help by passing -h as argument:

[source,bash]
----
usage: kb4it [-h] -sp SOURCE_PATH [-tp TARGET_PATH] [-log LOGLEVEL]
             [--version]

KB4IT by Tomás Vírseda

optional arguments:
  -h, --help            show this help message and exit
  -sp SOURCE_PATH, --source-path SOURCE_PATH
                        Path for Asciidoctor source files.
  -tp TARGET_PATH, --target-path TARGET_PATH
                        Path for output files
  -log LOGLEVEL, --log-level LOGLEVEL
                        Increase output verbosity
  --version             show program's version number and exit

----

`-sp` is mandatory. KB4IT needs to know where your sources are.

`-tp` is optional. If this parameter is missing, a directory `target` will be created. If it exists, contents will be deleted.

`-log` accepts DEBUG, INFO, WARNING, and ERROR



== Notes

* Target directory is created if it does not exist.
* Source directory is never touched. Source documents are copied to a temporary directory
* Contents on target directory are always deleted after compilation and replace it with those in the cache and the new ones compiled.

== Download

Get the code from GitHub:

[source,bash]
----
git clone https://github.com/t00m/KB4IT
----


== Credits

* https://python.org[Python]
* https://asciidoctor.org[Asciidoctor]
* https://getuikit.com[UIKit]
