from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


# Load modules for compatibility
from niworkflows.interfaces import bids

from .defacing_algorithms import run_pydeface, run_mri_deface, run_mridefacer, run_quickshear

from .workflow_description import SubjectSummary, AboutSummary

from .utils import copy_no_deid, check_meta_data, del_meta_data

class DerivativesDataSink(bids.DerivativesDataSink):
    out_path_base = 'bidsonym'


__all__ = [
    'bids',
    'run_pydeface',
    'run_mri_deface',
    'run_mridefacer',
    'run_quickshear',
    'DerivativesDataSink',
    'SubjectSummary',
    'AboutSummary',
    'copy_no_deid',
    'check_meta_data',
    'del_meta_data',
]
