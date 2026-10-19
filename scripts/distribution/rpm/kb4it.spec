# kb4it.spec - RPM spec for KB4IT
#
# Built by build_rpm.sh, which passes every value through rpmbuild --define:
#   kb4it_version, kb4it_release   RPM does not allow '+' in Version, so semver build
#                                  metadata (e.g. 0.7.31+build.0) goes to Release (build.0)
#   kb4it_summary, kb4it_description, kb4it_pythons   from lib/common.sh
#   kb4it_python_requires          the boolean Python dependency built from kb4it_pythons
#   kb4it_wheel                    file name of the KB4IT wheel (Source1)
#
# Packaging style: same as the .deb. The package carries the KB4IT wheel and the
# wheels of its dependencies; %post installs them into a private virtualenv under
# /opt/kb4it/venv without network access and links /usr/bin/kb4it. The wheels hold
# compiled code (lxml, PyYAML, MarkupSafe), so the package is per architecture.

%global debug_package %{nil}
# The payload is wheel files: nothing to strip, byte-compile or scan for dependencies.
%global __os_install_post %{nil}

Name:           kb4it
Version:        %{kb4it_version}
Release:        %{kb4it_release}%{?dist}
Summary:        %{kb4it_summary}

License:        GPL-3.0-or-later
URL:            https://github.com/t00m/KB4IT
Source0:        %{name}-%{version}-docs.tar.gz
Source1:        %{kb4it_wheel}
Source2:        %{name}-%{version}-wheels-%{_target_cpu}.tar.gz

AutoReqProv:    no
Requires:       %{kb4it_python_requires}

%description
%{kb4it_description}

%prep
%setup -q -c -n %{name}-%{version}

%build
# Nothing to build: the wheels are built by build_rpm.sh before rpmbuild runs.

%install
install -d %{buildroot}/opt/%{name}/wheels
install -m 0644 %{SOURCE1} %{buildroot}/opt/%{name}/wheels/
tar -xzf %{SOURCE2} -C %{buildroot}/opt/%{name}/wheels

%post
VENV_DIR=/opt/%{name}/venv
SUPPORTED="%{kb4it_pythons}"
PY=""
# Newest supported interpreter first; python3 last, for distributions where it is recent.
for candidate in $(for v in $SUPPORTED; do echo "python$v"; done | sort -r -V) python3; do
    command -v "$candidate" >/dev/null 2>&1 || continue
    version=$("$candidate" -c 'import sys; print("%%d.%%d" %% sys.version_info[:2])')
    case " $SUPPORTED " in
        *" $version "*) PY=$(command -v "$candidate"); break ;;
    esac
done
if [ -z "$PY" ]; then
    echo "kb4it: no supported Python found; install one of: $SUPPORTED" >&2
    exit 1
fi
PREVIOUS=$(cat /opt/%{name}/python 2>/dev/null || true)
if [ -n "$PREVIOUS" ] && [ "$PREVIOUS" != "$PY" ]; then
    echo "kb4it: Python changed from $PREVIOUS to $PY"
fi
echo "kb4it: creating $VENV_DIR with $PY ($version)"
rm -rf "$VENV_DIR"
"$PY" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --quiet --disable-pip-version-check --no-cache-dir \
    --no-index --find-links /opt/%{name}/wheels "%{name}==%{kb4it_wheel_version}"
echo "$PY" > /opt/%{name}/python
ln -sf "$VENV_DIR/bin/kb4it" %{_bindir}/%{name}

%preun
# Before RPM removes the package files, so /opt/kb4it is empty and goes too.
if [ "$1" = 0 ]; then
    rm -f %{_bindir}/%{name}
    rm -rf /opt/%{name}/venv /opt/%{name}/python
fi

%files
%license LICENSE
%doc README.md CHANGELOG.md AUTHORS THANKS
%dir /opt/%{name}
/opt/%{name}/wheels

%changelog
* Mon Oct 12 2026 Tomás Vírseda <tomasvirseda@gmail.com> - %{version}-%{release}
- Ship the dependency wheels and install offline; support RHEL 9 through python3.11 or newer
* Sun Apr 19 2026 Tomás Vírseda <tomasvirseda@gmail.com> - 0.7.31-1
- Packaged via scripts/distribution/rpm/build_rpm.sh
