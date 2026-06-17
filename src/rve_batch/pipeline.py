"""Single-case RVE pipeline orchestration.

Planned stages:
1. build TexGen model
2. export raw VTU
3. fix VTU node order
4. add Material CellData
5. generate solver config
6. run solver
7. collect summary
"""


def run_single_case(case_config):
    """Run one RVE case from modelling to result collection."""
    raise NotImplementedError
