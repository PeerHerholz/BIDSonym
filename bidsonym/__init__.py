from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from .defacing_algorithms import run_pydeface, run_mri_deface, run_mridefacer, run_quickshear

from .utils import copy_no_deid, check_meta_data, del_meta_data


__all__ = [
    'run_pydeface',
    'run_mri_deface',
    'run_mridefacer',
    'run_quickshear',
    'copy_no_deid',
    'check_meta_data',
    'del_meta_data',
]
