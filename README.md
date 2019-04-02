Introduction {#_introduction}
============

**KB4IT** helps you to build a static website with all your procedures
and documents

It is based on [Asciidoctor](https://asciidoctor.org) markdown.

Main goals:

-   Easy to [write](kb4it_write.xml) technical documentation

-   Easy to [find](kb4it_find.xml) documentation

-   Easy to [publish](kb4it_publish.xml) documentation

-   Easy to [backup/restore](kb4it_expimp.xml) documentation

How it works {#_how_it_works}
============

There is only one script (kb4it.py) which is in charge of all process.

This is the flow:

1.  Delete contents of target directory (if any)

2.  Get source documents

3.  Preprocess documents (get metadata)

4.  Process documents in a temporary dir

5.  Compile documents to html with asciidoc

6.  Copy all documents to target path

7.  Copy source docs to target directory

The code is organized in the following way:

    ├── kb4it.py
    ├── README
    ├── resources
    │   ├── offline
    │   │   └── templates
    │   │       ├── TPL_METADATA_SECTION_BODY.tpl
    │   │       ├── TPL_METADATA_SECTION_FOOTER.tpl
    │   │       ├── TPL_METADATA_SECTION_HEADER.tpl
    │   │       ├── TPL_TOP_NAV_BAR.tpl
    │   │       ├── TPL_INDEX_ALL.tpl
    │   │       ├── TPL_INDEX.tpl
    │   │       ├── TPL_KEY_PAGE.tpl
    │   │       ├── TPL_KEYS.tpl
    │   │       ├── TPL_METAKEY.tpl
    │   │       ├── TPL_METAVALUE.tpl
    │   │       └── TPL_VALUE.tpl
    │   └── online
    │       ├── css
    │       │   ├── coderay-asciidoctor.css
    │       │   └── kb4it.css
    │       ├── images
    │       └── js
    └── source
        ├── kb4it_about.adoc
        ├── kb4it_expimp.adoc
        ├── kb4it_find.adoc
        ├── kb4it_publish.adoc
        └── kb4it_write.adoc

Resources directory contains another two directories:

-   offline: resources used to help build target files

-   online: resources to be copied to target directory

Execution {#_execution}
=========

kb4it is a python 3 script. All parameters are optional.

The most typical usage would be:

    python3 kb4it.py -sp /path/to/source/docs -tp /var/www/html/repo -v ERROR

Display help by passing -h as argument:

``` {.bash}
usage: kb4it.py [-h] [-sp SOURCE_PATH] [-tp TARGET_PATH] [-v LOGLEVEL [DEBUG|INFO|ERROR]]
                [--version]

KB4IT by Tomás Vírseda

optional arguments:
  -h, --help            show this help message and exit
  -sp SOURCE_PATH, --source-path SOURCE_PATH
                        Path for Asciidoc source files.
  -tp TARGET_PATH, --target-path TARGET_PATH
                        Path for output files
  -v LOGLEVEL, --verbosity LOGLEVEL
                        Increase output verbosity
  --version             show program's version number and exit
```

After execute the script (with LOGLEVEL=INFO), you should get an output
similar to this:

       INFO |  818  | 2018-08-30 23:05:39,196 | KB4IT - Knowledge Base for IT
       INFO |  803  | 2018-08-30 23:05:39,210 | 1. Target directory clean
       INFO |  827  | 2018-08-30 23:05:39,211 | 2. Got 68 docs from source directory
       INFO |  775  | 2018-08-30 23:05:39,345 | 3. Preprocessed 68 docs
       INFO |  489  | 2018-08-30 23:05:43,079 | 4. Document's metadata processed
       INFO |  632  | 2018-08-30 23:05:44,488 |     Compiling:   5% done
       INFO |  632  | 2018-08-30 23:05:45,726 |     Compiling:  10% done
       INFO |  632  | 2018-08-30 23:05:47,112 |     Compiling:  15% done
       INFO |  632  | 2018-08-30 23:05:48,260 |     Compiling:  20% done
       INFO |  632  | 2018-08-30 23:05:49,324 |     Compiling:  25% done
       INFO |  632  | 2018-08-30 23:05:50,504 |     Compiling:  30% done
       INFO |  632  | 2018-08-30 23:05:51,804 |     Compiling:  36% done
       INFO |  632  | 2018-08-30 23:05:52,889 |     Compiling:  41% done
       INFO |  632  | 2018-08-30 23:05:54,109 |     Compiling:  46% done
       INFO |  632  | 2018-08-30 23:05:55,345 |     Compiling:  51% done
       INFO |  632  | 2018-08-30 23:05:56,709 |     Compiling:  56% done
       INFO |  632  | 2018-08-30 23:05:57,909 |     Compiling:  61% done
       INFO |  632  | 2018-08-30 23:05:59,069 |     Compiling:  67% done
       INFO |  632  | 2018-08-30 23:06:00,192 |     Compiling:  72% done
       INFO |  632  | 2018-08-30 23:06:01,375 |     Compiling:  77% done
       INFO |  632  | 2018-08-30 23:06:02,376 |     Compiling:  82% done
       INFO |  632  | 2018-08-30 23:06:03,556 |     Compiling:  87% done
       INFO |  632  | 2018-08-30 23:06:04,801 |     Compiling:  92% done
       INFO |  632  | 2018-08-30 23:06:05,780 |     Compiling:  97% done
       INFO |  633  | 2018-08-30 23:06:05,890 |     Compiling: 100% done
       INFO |  634  | 2018-08-30 23:06:05,890 | 5. Documents compiled successfully.
       INFO |  789  | 2018-08-30 23:06:05,987 | 6. Compiled documents copied to target directory
       INFO |  853  | 2018-08-30 23:06:06,000 | 7. Source docs copied to target directory
       INFO |  854  | 2018-08-30 23:06:06,000 | Execution finished

Notes {#_notes}
-----

> **Tip**
>
> Source and target directories are created if they do not exist.

> **Important**
>
> Source directory is never touched. Source documents are copied to a
> temporary directory

> **Warning**
>
> Contents on target directory are always deleted before compilation

Download {#_download}
========

Get a copy from SVN repository:

``` {.bash}
git clone https://github.com/t00m/KB4IT.git
```
