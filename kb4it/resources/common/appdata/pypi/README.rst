About KB4IT
===========

Introduction
^^^^^^^^^^^^

*KB4IT* is a static website generator based on Asciidoctor sources
mainly for technical documentation purposes.

Motivations
^^^^^^^^^^^
-  The main aim is to provide an easy way to write technical
   documentation.
-  Don't care about the formatting and focus on the contents.
-  To allow teams to manage their knowledge database easily.
-  Do not depend on third software products like word processors or
   complex web applications.

Features
^^^^^^^^

Pros
""""

- Writing documentation: Documents must be in Asciidoctor format which is easy to learn.
- Finding documents: Once a document is converted to html, properties can be browsed. Moreover, property pages have filters and a search entry to filter by title.
- Publishing your repository: all necessary files are inside a directory. Browse it or copy it to your web server.
- Serverless: There is no need for a web server. Of course, you can use one if you please.
- Smart compiling: Only those documents added or modified are compiled.

Cons
""""

- No online editor: At this moment, KB4IT doesn't include any online editor. You must create or edit your documents with your preferred editor.
- No dynamic search: KB4IT was developed to be as simple as possible. No dependencies at all excepting Asciidoctor (as text processor and publishing toolchain) and Python (the programming language used).

Installation
^^^^^^^^^^^^

From source
"""""""""""

``python3 setup.py install --user``

Pypi package
""""""""""""

``pip3 install kb4it --user``

Execution
^^^^^^^^^

The most typical usage would be:

``$HOME/.local/bin/kb4it -sp /path/to/asciidoctor/sources -tp /path/to/target/directory --log DEBUG``

Download
^^^^^^^^

Get the code from GitHub:

``git clone https://github.com/t00m/KB4IT``


Credits
^^^^^^^

-  `Python <https://python.org>`_
-  `Asciidoctor <https://asciidoctor.org>`_
-  `UIKit <https://getuikit.com>`_
