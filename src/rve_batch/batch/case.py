"""Case directory and status management."""


def create_case_dir(case_id, results_root):
    """Create and return a case working directory."""
    raise NotImplementedError


def write_case_status(case_dir, status):
    """Write status.json for a case."""
    raise NotImplementedError
