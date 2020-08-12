import nipype.pipeline.engine as pe
from nipype import Function
from nipype.interfaces import utility as niu
from nipype.interfaces.quickshear import Quickshear
from nipype.interfaces.fsl import BET, FLIRT


def pydeface_cmd(image, outfile):

    from subprocess import check_call

    cmd = ["pydeface", image,
           "--out", outfile,
           "--force",
           ]
    check_call(cmd)
    return


def run_pydeface(image, outfile):

    deface_wf = pe.Workflow('deface_wf')
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    pydeface = pe.Node(Function(input_names=['image', 'outfile'],
                                output_names=['outfile'],
                                function=pydeface_cmd),
                       name='pydeface')
    deface_wf.connect([(inputnode, pydeface, [('in_file', 'image')])])
    inputnode.inputs.in_file = image
    pydeface.inputs.outfile = outfile
    deface_wf.run()


def mri_deface_cmd(image, outfile):

    from subprocess import check_call

    cmd = ["/home/bm/bidsonym/fs_data/mri_deface",
           image,
           '/home/bm/bidsonym/fs_data/talairach_mixed_with_skull.gca',
           '/home/bm/bidsonym/fs_data/face.gca',
           outfile,
           ]
    check_call(cmd)
    return


def run_mri_deface(image, outfile):

    deface_wf = pe.Workflow('deface_wf')
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    mri_deface = pe.Node(Function(input_names=['image', 'outfile'],
                                  output_names=['outfile'],
                                  function=mri_deface_cmd),
                         name='mri_deface')
    deface_wf.connect([(inputnode, mri_deface, [('in_file', 'image')])])
    inputnode.inputs.in_file = image
    mri_deface.inputs.outfile = outfile
    deface_wf.run()


def run_quickshear(image, outfile):

    deface_wf = pe.Workflow('deface_wf')
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    bet = pe.Node(BET(mask=True, frac=0.5), name='bet')
    quickshear = pe.Node(Quickshear(buff=50), name='quickshear')
    deface_wf.connect([
        (inputnode, bet, [('in_file', 'in_file')]),
        (inputnode, quickshear, [('in_file', 'in_file')]),
        (bet, quickshear, [('mask_file', 'mask_file')]),
        ])
    inputnode.inputs.in_file = image
    quickshear.inputs.out_file = outfile
    deface_wf.run()


def mridefacer_cmd(image, subject_label, bids_dir):

    from subprocess import check_call
    import os
    from shutil import move

    cmd = ["/mridefacer/mridefacer", "--apply", image]
    check_call(cmd)
    path = os.path.join(bids_dir, "sourcedata/bidsonym/sub-%s" % subject_label)
    facemask = os.path.join(bids_dir, "sub-%s" % subject_label,
                            "anat/sub-%s_T1w_defacemask.nii.gz" % subject_label)
    if os.path.isdir(path) is True:
        move(facemask, os.path.join(path))
    else:
        os.makedirs(path)
        move(facemask, os.path.join(path))
    return


def run_mridefacer(image, subject_label, bids_dir):

    deface_wf = pe.Workflow('deface_wf')
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    mridefacer = pe.Node(Function(input_names=['image', 'subject_label', 'bids_dir'],
                                  output_names=['outfile'],
                                  function=mridefacer_cmd),
                         name='mridefacer')
    deface_wf.connect([(inputnode, mridefacer, [('in_file', 'image')])])
    inputnode.inputs.in_file = image
    mridefacer.inputs.subject_label = subject_label
    mridefacer.inputs.bids_dir = bids_dir
    deface_wf.run()


def deepdefacer_cmd(image, subject_label, bids_dir):

    import os
    from subprocess import check_call

    maskfile = os.path.join(bids_dir,
                            "sourcedata/bidsonym/sub-%s/sub-%s_T1w_space-native_defacemask-deepdefacer"
                            % (subject_label, subject_label))

    cmd = ["deepdefacer", "--input_file", image,
           "--defaced_output_path", image,
           "--mask_output_path", maskfile]
    check_call(cmd)


def run_deepdefacer(image, subject_label, bids_dir):

    deface_wf = pe.Workflow('deface_wf')
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    deepdefacer = pe.Node(Function(input_names=['image', 'subject_label', 'bids_dir'],
                                   output_names=['outfile'],
                                   function=deepdefacer_cmd),
                          name='deepdefacer')
    deface_wf.connect([(inputnode, deepdefacer, [('in_file', 'image')])])
    inputnode.inputs.in_file = image
    deepdefacer.inputs.subject_label = subject_label
    deepdefacer.inputs.bids_dir = bids_dir
    deface_wf.run()


def run_t2w_deface(image, t1w_deface_mask, outfile):

    from bidsonym.utils import deface_t2w

    deface_wf = pe.Workflow('deface_wf')
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    flirtnode = pe.Node(FLIRT(cost_func='mutualinfo',
                              output_type="NIFTI_GZ"),
                        name='flirtnode')
    deface_t2w = pe.Node(Function(input_names=['image', 'warped_mask', 'outfile'],
                                  output_names=['outfile'],
                                  function=deface_t2w),
                         name='deface_t2w')
    deface_wf.connect([(inputnode, flirtnode, [('in_file', 'reference')]),
                       (inputnode, deface_t2w, [('in_file', 'image')]),
                       (flirtnode, deface_t2w, [('out_file', 'warped_mask')])])
    inputnode.inputs.in_file = image
    flirtnode.inputs.in_file = t1w_deface_mask
    deface_t2w.inputs.outfile = outfile
    deface_wf.run()
