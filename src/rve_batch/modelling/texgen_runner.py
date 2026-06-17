"""Helpers for running TexGen scripts/API without modifying TexGen source."""


def setup_texgen_api(texgen_lib_path):
    """Add TexGen Python API path to sys.path."""
    raise NotImplementedError


def run_texgen_script(script_path, texgen_gui_exe=None):
    """Run an external TexGen script through TexGen GUI/CLI when needed."""
    raise NotImplementedError
