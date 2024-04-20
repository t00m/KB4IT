configure_file(
  input: 'kb4it.py',
  output: 'kb4it',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr--r--'
)

# Python sources
sources = [
  'main.py'
]

install_data(sources, install_dir: moduledir)

# Subpackages
install_subdir('core', install_dir: moduledir)
install_subdir('services', install_dir: moduledir)
