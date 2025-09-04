import nipype.pipeline.engine as pe
from nipype import Function
from nipype.interfaces import utility as niu
from nipype.interfaces.quickshear import Quickshear
from nipype.interfaces.fsl import BET, FLIRT
from bidsonym.utils import deface_image


def pydeface_cmd(image, outfile):
    """
    Setup pydeface command.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    outfile : str
        Name of the defaced file.
    """

    from subprocess import check_call

    # Construct pydeface command using subprocess
    # pydeface is a Python-based defacing tool that removes facial features
    cmd = ["pydeface", image,        # Input image file
           "--out", outfile,         # Specify output file path
           "--force",                # Overwrite existing output files
           ]
    
    # Execute the pydeface command
    # check_call will raise an exception if the command fails
    check_call(cmd)
    return


def run_pydeface(image, outfile):
    """
    Setup and run pydeface workflow.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    outfile : str
        Name of the defaced file.
    """

    # Create a Nipype workflow for pydeface processing
    deface_wf = pe.Workflow('deface_wf')
    
    # Create input node to handle data flow
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    
    # Create a function node that wraps the pydeface_cmd function
    # This integrates the external pydeface tool into the Nipype workflow
    pydeface = pe.Node(Function(input_names=['image', 'outfile'],
                                output_names=['outfile'],
                                function=pydeface_cmd),
                       name='pydeface')
    
    # Connect input node to pydeface node (data flow)
    deface_wf.connect([(inputnode, pydeface, [('in_file', 'image')])])
    
    # Set workflow inputs
    inputnode.inputs.in_file = image
    pydeface.inputs.outfile = outfile
    
    # Execute the workflow
    deface_wf.run()


def mri_deface_cmd(image, outfile):
    """
    Setup mri_deface command.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    outfile : str
        Name of the defaced file.
    """

    from subprocess import check_call

    # Construct mri_deface command (FreeSurfer's defacing tool)
    # Uses atlas-based approach with Talairach registration and face template
    cmd = ["/home/bm/bidsonym/fs_data/mri_deface",                    # mri_deface executable
           image,                                                     # Input T1w image
           '/home/bm/bidsonym/fs_data/talairach_mixed_with_skull.gca',  # Atlas for brain registration
           '/home/bm/bidsonym/fs_data/face.gca',                      # Face template for detection
           outfile,                                                   # Output defaced image
           ]
    
    # Execute the mri_deface command
    check_call(cmd)
    return


def run_mri_deface(image, outfile):
    """
    Setup and run mri_deface workflow.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    outfile : str
        Name of the defaced file.
    """

    # Create a Nipype workflow for mri_deface processing
    deface_wf = pe.Workflow('deface_wf')
    
    # Create input node for data flow
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    
    # Create function node that wraps mri_deface_cmd
    # Integrates FreeSurfer's mri_deface tool into Nipype workflow
    mri_deface = pe.Node(Function(input_names=['image', 'outfile'],
                                  output_names=['outfile'],
                                  function=mri_deface_cmd),
                         name='mri_deface')
    
    # Connect workflow nodes
    deface_wf.connect([(inputnode, mri_deface, [('in_file', 'image')])])
    
    # Set workflow inputs
    inputnode.inputs.in_file = image
    mri_deface.inputs.outfile = outfile
    
    # Execute the workflow
    deface_wf.run()


def run_quickshear(image, outfile):
    """
    Setup and run quickshear workflow.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    outfile : str
        Name of the defaced file.
    """

    # Create workflow for Quickshear defacing method
    # Quickshear uses brain extraction + geometric face removal
    deface_wf = pe.Workflow('deface_wf')
    
    # Create input node
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    
    # Create BET node for brain extraction
    # mask=True generates binary brain mask, frac=0.5 sets intensity threshold
    bet = pe.Node(BET(mask=True, frac=0.5), name='bet')
    
    # Create Quickshear node for face removal
    # buff=50 sets buffer size around face removal region
    quickshear = pe.Node(Quickshear(buff=50), name='quickshear')
    
    # Connect workflow nodes
    # Both BET and Quickshear receive the original image
    # Quickshear also receives the brain mask from BET
    deface_wf.connect([
        (inputnode, bet, [('in_file', 'in_file')]),              # Input -> BET
        (inputnode, quickshear, [('in_file', 'in_file')]),       # Input -> Quickshear
        (bet, quickshear, [('mask_file', 'mask_file')])          # BET mask -> Quickshear
    ])
    
    # Set workflow inputs
    inputnode.inputs.in_file = image
    quickshear.inputs.out_file = outfile
    
    # Execute the workflow
    deface_wf.run()


def mridefacer_cmd(image, T1_file):
    """
    Setup mridefacer command.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    T1_file : str
        Path to reference T1-weighted image.
    """

    from subprocess import check_call

    # Extract output directory from T1_file path
    # mridefacer writes output to the same directory as the reference T1
    outdir = T1_file[:T1_file.rfind('/')]

    # Construct mridefacer command
    # Uses deep learning approach for face detection and removal
    cmd = ["/mridefacer/mridefacer",    # mridefacer executable
           "--apply", image,            # Apply defacing to this image
           "--outdir", outdir]          # Output directory
    
    # Execute the mridefacer command
    check_call(cmd)
    return


def run_mridefacer(image, T1_file):
    """
    Setup and run mridefacer workflow.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    T1_file : str
        Path to reference T1-weighted image.
    """

    # Create Nipype workflow for mridefacer processing
    deface_wf = pe.Workflow('deface_wf')
    
    # Create input node
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    
    # Create function node that wraps mridefacer_cmd
    # Integrates mridefacer deep learning tool into workflow
    mridefacer = pe.Node(Function(input_names=['image', 'T1_file'],
                                  output_names=['outfile'],
                                  function=mridefacer_cmd),
                         name='mridefacer')
    
    # Connect workflow nodes
    deface_wf.connect([(inputnode, mridefacer, [('in_file', 'image')])])
    
    # Set workflow inputs
    inputnode.inputs.in_file = image
    mridefacer.inputs.T1_file = T1_file
    
    # Execute the workflow
    deface_wf.run()


def deepdefacer_cmd(image, subject_label, bids_dir):
    """
    Setup deepdefacer command.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    subject_label : str
        Label of subject to operate on (without 'sub-').
    bids_dir : str
        Path to BIDS root directory.
    """

    import os
    from subprocess import check_call

    # Construct path for defacing mask output
    # deepdefacer can output both defaced image and binary mask
    maskfile = os.path.join(bids_dir,
                            "sourcedata/bidsonym/sub-%s/sub-%s_T1w_space-native_defacemask-deepdefacer"
                            % (subject_label, subject_label))

    # Construct deepdefacer command
    # Uses deep learning (U-Net) for face detection and removal
    cmd = ["deepdefacer",                           # deepdefacer executable
           "--input_file", image,                   # Input image to deface
           "--defaced_output_path", image,          # Overwrite input with defaced version
           "--mask_output_path", maskfile]          # Save defacing mask separately
    
    # Execute the deepdefacer command
    check_call(cmd)


def run_deepdefacer(image, subject_label, bids_dir):
    """
    Setup and run deepdefacer workflow.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    subject_label : str
        Label of subject to operate on (without 'sub-').
    bids_dir : str
        Path to BIDS root directory.
    """

    # Create Nipype workflow for deepdefacer processing
    deface_wf = pe.Workflow('deface_wf')
    
    # Create input node
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    
    # Create function node that wraps deepdefacer_cmd
    # Integrates deepdefacer deep learning tool into workflow
    deepdefacer = pe.Node(Function(input_names=['image', 'subject_label', 'bids_dir'],
                                   output_names=['outfile'],
                                   function=deepdefacer_cmd),
                          name='deepdefacer')
    
    # Connect workflow nodes
    deface_wf.connect([(inputnode, deepdefacer, [('in_file', 'image')])])
    
    # Set workflow inputs
    inputnode.inputs.in_file = image
    deepdefacer.inputs.subject_label = subject_label
    deepdefacer.inputs.bids_dir = bids_dir
    
    # Execute the workflow
    deface_wf.run()


def run_image_deface(image, t1w_deface_mask, outfile):
    """
    Setup and run image defacing workflow.

    Parameters
    ----------
    image : str
        Path to image that should be defaced.
    t1w_deface_mask : str
        Path to the defaced T1w image that will be used
        as defacing mask.
    outfile : str
        Name of the defaced file.
    """

    # Create workflow for applying T1w defacing mask to other image modalities
    # This allows defacing of non-T1w images using a T1w-derived mask
    deface_wf = pe.Workflow('deface_wf')
    
    # Create input node
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                        name='inputnode')
    
    # Create FLIRT node for image registration
    # Registers the T1w defacing mask to the target image space
    # Uses mutual information cost function for robust cross-modal registration
    flirtnode = pe.Node(FLIRT(cost_func='mutualinfo',
                              output_type="NIFTI_GZ"),
                        name='flirtnode')
    
    # Create deface_image node using the custom deface_image function
    # Applies the registered defacing mask to remove facial features
    deface_image_node = pe.Node(Function(input_names=['image', 'warped_mask', 'outfile'],
                                         output_names=['outfile'],
                                         function=deface_image),
                                name='deface_image')
    
    # Connect workflow nodes
    # FLIRT registers T1w mask to target image space
    # deface_image applies the warped mask to remove facial features
    deface_wf.connect([(inputnode, flirtnode, [('in_file', 'reference')]),      # Target image as reference
                       (inputnode, deface_image_node, [('in_file', 'image')]),        # Target image to deface
                       (flirtnode, deface_image_node, [('out_file', 'warped_mask')])])  # Registered mask
    
    # Set workflow inputs
    inputnode.inputs.in_file = image              # Image to be defaced
    flirtnode.inputs.in_file = t1w_deface_mask    # T1w defacing mask to register
    deface_image_node.inputs.outfile = outfile          # Output file path
    
    # Execute the workflow
    deface_wf.run()
