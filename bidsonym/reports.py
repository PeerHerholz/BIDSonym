import os
import time

from glob import glob
import matplotlib.pyplot as plt
from matplotlib import figure


from nipype.interfaces.base import (
    TraitedSpec, BaseInterfaceInputSpec,
    File, Directory, InputMultiObject, Str, isdefined,
    SimpleInterface)
from nilearn.plotting import plot_anat, find_cut_slices
import nibabel as nb
from niworkflows.utils.bids import BIDS_NAME


SUBJECT_TEMPLATE = """\
\t<ul class="elem-desc">
\t\t<li>Subject ID: {subject_id}</li>
\t\t<li>Structural images: {n_t1s:d} T1-weighted {t2w}</li>
"""

ABOUT_TEMPLATE = """\t<ul>
\t\t<li>BIDSonym version: {version}</li>
\t\t<li>BIDSonym command: <code>{command}</code></li>
\t\t<li>Date preprocessed: {date}</li>
\t</ul>
</div>
"""


class SummaryOutputSpec(TraitedSpec):
    out_report = File(exists=True, desc='HTML segment containing summary')


class SummaryInterface(SimpleInterface):
    output_spec = SummaryOutputSpec

    def _run_interface(self, runtime):
        segment = self._generate_segment()
        fname = os.path.join(runtime.cwd, 'report.html')
        with open(fname, 'w') as fobj:
            fobj.write(segment)
        self._results['out_report'] = fname
        return runtime

    def _generate_segment(self):
        raise NotImplementedError


class SubjectSummaryInputSpec(BaseInterfaceInputSpec):
    t1w = InputMultiObject(File(exists=True), desc='T1w structural images')
    t2w = InputMultiObject(File(exists=True), desc='T2w structural images')
    subjects_dir = Directory(desc='FreeSurfer subjects directory')
    subject_id = Str(desc='Subject ID')


class SubjectSummary(SummaryInterface):
    input_spec = SubjectSummaryInputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.subject_id):
            self._results['subject_id'] = self.inputs.subject_id
        return super(SubjectSummary, self)._run_interface(runtime)

    def _generate_segment(self):

        return SUBJECT_TEMPLATE.format(
            subject_id=self.inputs.subject_id,
            n_t1s=len(self.inputs.t1w))


class AboutSummaryInputSpec(BaseInterfaceInputSpec):
    version = Str(desc='BIDSonym version')
    command = Str(desc='BIDSonym command')
    # Date not included - update timestamp only if version or command changes


class AboutSummary(SummaryInterface):
    input_spec = AboutSummaryInputSpec

    def _generate_segment(self):
        return ABOUT_TEMPLATE.format(version=self.inputs.version,
                                     command=self.inputs.command,
                                     date=time.strftime("%Y-%m-%d %H:%M:%S %z"))


def plot_static_defaced(bids_dir, subject_id):

    defaced_img = nb.load(glob(os.path.join(bids_dir, 'sub-%s' % subject_id, 'anat/*T1w.nii.gz'))[0])
    defaced_plot = plot_anat(defaced_img,
                             draw_cross=False,
                             annotate=False,
                             output_file=os.path.join(bids_dir,
                                                      'sourcedata/bidsonym/sub-%s/sub-%s_deface_static.png'
                                                      % (subject_id, subject_id)))

    f, (ax1, ax2, ax3) = plt.subplots(3)
    plot_anat(defaced_img, draw_cross=False, annotate=False, display_mode='x', cut_coords=8, ax=ax1)
    plot_anat(defaced_img, draw_cross=False, annotate=False, display_mode='y', cut_coords=8, ax=ax2)
    plot_anat(defaced_img, draw_cross=False, annotate=False, display_mode='z', cut_coords=8)
    plt.show()

    fig = figure(figsize=(12, 7))
    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=-0.2, hspace=0)
    for i, e in enumerate(['x', 'y', 'z']):
        ax = fig.add_subplot(3, 1, i + 1)
        cuts = find_cut_slices(defaced_img, direction=e, n_cuts=12)[2:-2]
        plot_anat(defaced_img, display_mode=e,
                  cut_coords=cuts, annotate=False, axes=ax, dim=-1)
    plt.show()
