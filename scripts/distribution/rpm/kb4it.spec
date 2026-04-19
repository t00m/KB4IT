# kb4it.spec — RPM spec for KB4IT
#
# Release convention: RPM does not allow '+' in Version, so semver build
# metadata (e.g. 0.7.31+build.0) is remapped to Release (build.0) at build
# time by build_rpm.sh. The %{kb4it_version} / %{kb4it_release} macros are
# passed via rpmbuild --define.
#
# Packaging style: same as the .deb — install the wheel into a private
# virtualenv under /opt/kb4it/venv and expose /usr/bin/kb4it as a symlink.

%global debug_package %{nil}
%global _python_bytecompile_errors_terminate_build 0

Name:           kb4it
Version:        %{kb4it_version}
Release:        %{kb4it_release}%{?dist}
Summary:        Static website generator for technical documentation based on Asciidoctor

License:        GPL-3.0-or-later
URL:            https://github.com/t00m/KB4IT
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3 >= 3.11
BuildRequires:  python3-pip

Requires:       python3 >= 3.11
Requires:       asciidoctor

%description
KB4IT converts AsciiDoc sources into a static website using Mako
templates. It supports multiple themes (techdoc, book, blog) and
incremental compilation via file hashing.

%prep
%setup -q -n %{name}-%{version}

%build
# The wheel is built in %install so we can stage it inside buildroot.

%install
rm -rf %{buildroot}
install -d %{buildroot}/opt/%{name}/wheel
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_docdir}/%{name}

python3 -m pip install --quiet --upgrade --user build
python3 -m build --wheel --outdir %{buildroot}/opt/%{name}/wheel
cp LICENSE %{buildroot}%{_docdir}/%{name}/
cp README.rst Changelog AUTHORS THANKS %{buildroot}%{_docdir}/%{name}/ 2>/dev/null || true

%post
VENV_DIR=/opt/%{name}/venv
WHEEL=$(ls /opt/%{name}/wheel/*.whl | head -n 1)
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet "$WHEEL"
ln -sf "$VENV_DIR/bin/kb4it" %{_bindir}/%{name}

%preun
if [ "$1" = 0 ]; then
    rm -f %{_bindir}/%{name}
fi

%postun
if [ "$1" = 0 ]; then
    rm -rf /opt/%{name}/venv
fi

%files
%license LICENSE
%doc README.rst Changelog AUTHORS THANKS
/opt/%{name}/wheel/*.whl

%changelog
* Sun Apr 19 2026 Tomás Vírseda <tomasvirseda@gmail.com> - %{version}-%{release}
- Packaged via scripts/distribution/rpm/build_rpm.sh
