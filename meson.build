project('kb4it',
          version: '0.0.1',
    meson_version: '>= 0.55.0',
  default_options: [ 'warning_level=2',
                   ],
)

#~ r = run_command('spacy', 'validate', check: true)
#~ output = r.stdout().strip()
#~ errortxt = r.stderr().strip()
#~ message(output)



python = import('python')
i18n = import('i18n')


profile = get_option('profile')
if profile == 'development'
  app_id = 'com.github.t00m.kb4it.Devel'
  prefix = '/com/github/t00m/kb4it/Devel'
elif profile == 'release'
  app_id = 'com.github.t00m.kb4it'
  prefix = '/com/github/t00m/kb4it'
endif

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'kb4it')
#~ revision = run_command('./build-aux/meson/revision.sh').stdout().strip()
#~ if revision == ''
#~   revision=meson.project_version()
#~ endif

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('PYTHON_VERSION', python.find_installation('python3').language_version())
conf.set('APP_ID', app_id)
conf.set('PREFIX', prefix)
conf.set('VERSION', meson.project_version())
#~ conf.set('REVISION', revision)
conf.set('PROFILE', profile)
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

subdir('data')
subdir('kb4it')
#~ subdir('po')

#~ meson.add_install_script('build-aux/meson/postinstall.py')
