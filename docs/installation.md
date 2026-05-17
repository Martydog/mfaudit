# Installation

## Requirements

- Python **3.9 or later**
- A Python virtual environment (recommended)

## Install via pip

```bash
pip install mfaudit
```

This installs the `mfaudit` CLI command and all required dependencies including **WeasyPrint** for PDF output.

### Pure-Python PDF fallback

If you cannot install the WeasyPrint system libraries (see below), xhtml2pdf provides PDF output with no native dependencies:

```bash
pip install "mfaudit[pdf-xhtml]"
```

MFAudit tries WeasyPrint first, then falls back to xhtml2pdf automatically. If neither renderer works, HTML and CSV output is still written.

## System libraries for WeasyPrint

=== "macOS (Homebrew)"

    ```bash
    brew install pango cairo gobject-introspection
    ```

=== "Debian / Ubuntu"

    ```bash
    sudo apt-get install -y \
        libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
        libcairo2 libcairo-gobject2 libgdk-pixbuf2.0-0 \
        libffi-dev shared-mime-info
    ```

=== "RHEL / CentOS"

    ```bash
    sudo yum install -y pango cairo gdk-pixbuf2 libffi
    ```

=== "Windows"

    Install the [GTK3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
    and add `C:\Program Files\GTK3-Runtime Win64\bin` to `PATH`.

    Alternatively use `pip install "mfaudit[pdf-xhtml]"` — xhtml2pdf needs no GTK.

## Get the controls library

The pip package installs the engine and CLI. The CIS and STIG control definitions (YAML files) live in the repository — clone it once to get them:

```bash
git clone https://github.com/wizardofzos/mfaudit.git
cd mfaudit
```

You can run `mfaudit` from any directory by passing full paths to `--controls`, `--irrdbu00`, and `--setropts`.

## Verify

```bash
mfaudit --help
```

## Installing for development

To work on MFAudit itself:

```bash
git clone https://github.com/wizardofzos/mfaudit.git
cd mfaudit
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[pdf]"
```
