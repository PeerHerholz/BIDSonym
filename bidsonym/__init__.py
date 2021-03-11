from ._version import get_versions

from .defacing_algorithms import run_pydeface, run_mri_deface, run_mridefacer, run_quickshear

from .utils import (check_outpath, copy_no_deid, check_meta_data, del_meta_data,
                    run_brain_extraction_nb, run_brain_extraction_bet, validate_input_dir)\

# from .reports import (plot_defaced, gif_defaced, run_reports)

__version__ = get_versions()['version']
del get_versions

__all__ = [
    'run_pydeface',
    'run_mri_deface',
    'run_mridefacer',
    'run_quickshear',
    'check_outpath',
    'copy_no_deid',
    'check_meta_data',
    'del_meta_data',
    'run_brain_extraction_nb',
    'run_brain_extraction_bet',
    'validate_input_dir',
]
