"""
Interfaces to generate reportlets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import os
import time
import re

from collections import Counter
from nipype.interfaces.base import (
    traits, TraitedSpec, BaseInterfaceInputSpec,
    File, Directory, InputMultiObject, Str, isdefined,
    SimpleInterface)
from nipype.interfaces import freesurfer as fs
from niworkflows.utils.bids import BIDS_NAME
from nipype import __version__ as nipype_ver
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nilearn import __version__ as nilearn_ver

from niworkflows.engine.workflows import LiterateWorkflow as Workflow

SUBJECT_TEMPLATE = """\
\t<ul class="elem-desc">
\t\t<li>Subject ID: {subject_id}</li>
\t\t<li>Structural images: {n_t1s:d} T1-weighted {t2w}</li>
\t\t<li>Meta data fields deleted: {meta_fields} </li>
\t\t<li>defacing algorithm used: {defacing_algorithm} {version_defacing}</li>
\t</ul>
"""

ABOUT_TEMPLATE = """\t<ul>
\t\t<li>BIDSonym version: {version}</li>
\t\t<li>BIDSonym command: <code>{command}</code></li>
\t\t<li>Date preprocessed: {date}</li>
\t</ul>
</div>
"""