#!@PYTHON@

# Copyright 2024 Tomás Vírseda
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import signal
import locale
import gettext
import argparse

from rich.traceback import install
# ~ install(show_locals=True)

sys.path.insert(1, '@pkgdatadir@')

from kb4it.main import main

# ~ ENV['APP'] = {}
# ~ ENV['APP']['ID'] = '@APP_ID@'
# ~ ENV['APP']['VERSION'] = '@VERSION@'
# ~ ENV['APP']['PGKDATADIR'] = '@pkgdatadir@'
# ~ ENV['APP']['LOCALEDIR'] = '@localedir@'

signal.signal(signal.SIGINT, signal.SIG_DFL)
gettext.install('kb4it', ENV['APP']['LOCALEDIR'])

try:
  locale.bindtextdomain('kb4it', ENV['APP']['LOCALEDIR'])
  locale.textdomain('kb4it')
  # ~ log.debug("Locales set")
except:
  log.error('Cannot set locale.')

try:
  gettext.bindtextdomain('kb4it', ENV['APP']['LOCALEDIR'])
  gettext.textdomain('kb4it')
  # ~ log.debug("Gettext set")
except:
  log.error('Cannot load translations.')


if __name__ == "__main__":
    extra_usage = """"""
    parser = argparse.ArgumentParser(
        prog='kb4it',
        description='%s v%s\nKnowledge Base builder for IT purposes' % (ENV['APP']['ID'], ENV['APP']['VERSION']),
        epilog=extra_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    kb4it_options = parser.add_argument_group('KB4IT options')
    params = parser.parse_args()
    main(params)
