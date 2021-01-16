def plot_defaced(bids_dir, subject_label, session=None, t2w=None):

    from bids import BIDSLayout
    from glob import glob
    from os.path import join as opj
    from matplotlib.pyplot import figure
    import matplotlib.pyplot as plt
    from nilearn.plotting import find_cut_slices, plot_stat_map

    layout = BIDSLayout(bids_dir)

    bidsonym_path = opj(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label)

    if session is not None:
        defaced_t1w = layout.get(subject=subject_label, extension='nii.gz', suffix='T1w',
                                 return_type='filename', session=session)
    else:
        defaced_t1w = layout.get(subject=subject_label, extension='nii.gz', suffix='T1w',
                                 return_type='filename')

    for t1w in defaced_t1w:
        brainmask_t1w = glob(opj(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label,
                                 t1w[t1w.rfind('/')+1:t1w.rfind('.nii')] +
                                 '_brainmask_desc-nondeid.nii.gz'))[0]
        fig = figure(figsize=(15, 5))
        plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=-0.2, hspace=0)
        for i, e in enumerate(['x', 'y', 'z']):
            ax = fig.add_subplot(3, 1, i + 1)
            cuts = find_cut_slices(t1w, direction=e, n_cuts=12)
            plot_stat_map(brainmask_t1w, bg_img=t1w, display_mode=e,
                          cut_coords=cuts, annotate=False, dim=-1, axes=ax, colorbar=False)
        plt.savefig(opj(bidsonym_path,
                        t1w[t1w.rfind('/')+1:t1w.rfind('.nii')] + '_desc-brainmaskdeid.png'))

    if t2w is not None:
        if session is not None:
            defaced_t2w = layout.get(subject=subject_label, extension='nii.gz', suffix='T2w',
                                     return_type='filename', session=session)
        else:
            defaced_t2w = layout.get(subject=subject_label, extension='nii.gz', suffix='T2w',
                                     return_type='filename')

        for t2w in defaced_t2w:
            brainmask_t2w = glob(opj(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label,
                                     t2w[t2w.rfind('/') + 1:t2w.rfind('.nii')] +
                                     '_brainmask_desc-nondeid.nii.gz'))[0]
            for i, e in enumerate(['x', 'y', 'z']):
                ax = fig.add_subplot(3, 1, i + 1)
                cuts = find_cut_slices(t2w, direction=e, n_cuts=12)
                plot_stat_map(brainmask_t2w, bg_img=t2w, display_mode=e,
                              cut_coords=cuts, annotate=False, dim=-1, axes=ax, colorbar=False)
            plt.savefig(opj(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label,
                            t2w[t2w.rfind('/')+1:t2w.rfind('.nii')] + '_desc-brainmaskdeid.png'))

    return (t1w, t2w)


def gif_defaced(bids_dir, subject_label, session=None, t2w=None):

    from bids import BIDSLayout
    from glob import glob
    from os.path import join as opj
    from shutil import move
    import gif_your_nifti.core as gif2nif

    layout = BIDSLayout(bids_dir)

    bidsonym_path = opj(bids_dir, 'sourcedata/bidsonym/sub-%s' % subject_label)

    if session is not None:
        defaced_t1w = layout.get(subject=subject_label, extension='nii.gz', suffix='T1w',
                                 return_type='filename', session=session)
        if t2w is not None:
            defaced_t2w = layout.get(subject=subject_label, extension='nii.gz', suffix='T2w',
                                     return_type='filename', session=session)
    else:
        defaced_t1w = layout.get(subject=subject_label, extension='nii.gz', suffix='T1w',
                                 return_type='filename')
        if t2w is not None:
            defaced_t2w = layout.get(subject=subject_label, extension='nii.gz', suffix='T2w',
                                     return_type='filename', session=session)

    for t1_image in defaced_t1w:
        gif2nif.write_gif_normal(t1_image)

    if t2w is not None:
        for t2_image in defaced_t2w:
            gif2nif.write_gif_normal(t2_image)

    if session is not None:
        list_gifs = glob(opj(bids_dir, 'sub-%s/ses-%s/anat' % (subject_label, session),
                             'sub-%s*.gif' % subject_label))
    else:
        list_gifs = glob(opj(bids_dir, 'sub-%s/anat' % subject_label,
                             'sub-%s*.gif' % subject_label))

    for gif_nii in list_gifs:
        move(gif_nii, opj(bids_dir, bidsonym_path))


def create_graphics(bids_dir, subject_label, session=None, t2w=None):

    import nipype.pipeline.engine as pe
    from nipype import Function
    from nipype.interfaces import utility as niu

    report_wf = pe.Workflow('report_wf')

    inputnode = pe.Node(niu.IdentityInterface(fields=['bids_dir', 'subject_label', 'session', 't2w']),
                        name='inputnode')
    plt_defaced = pe.Node(Function(input_names=['bids_dir', 'subject_label', 'session', 't2w'],
                                   function=plot_defaced),
                          name='plt_defaced')
    gf_defaced = pe.Node(Function(input_names=['bids_dir', 'subject_label', 'session', 't2w'],
                                  function=gif_defaced),
                         name='gf_defaced')

    report_wf.connect([(inputnode, plt_defaced, [('bids_dir', 'bids_dir'),
                                                 ('subject_label', 'subject_label')]),
                       (inputnode, gf_defaced, [('bids_dir', 'bids_dir'),
                                                ('subject_label', 'subject_label')]),
                       ])

    if session:
        inputnode.inputs.session = session
        report_wf.connect([(inputnode, plt_defaced, [('session', 'session')]),
                           (inputnode, gf_defaced, [('session', 'session')]),
                           ])

    if t2w:
        inputnode.inputs.t2w = t2w
        report_wf.connect([(inputnode, plt_defaced, [('t2w', 't2w')]),
                           (inputnode, gf_defaced, [('t2w', 't2w')]),
                           ])

    inputnode.inputs.bids_dir = bids_dir
    inputnode.inputs.subject_label = subject_label
    report_wf.run()
