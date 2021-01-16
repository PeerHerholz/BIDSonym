=====
Usage
=====


Execution and the BIDS format
=============================

The general input of ``BIDSonym`` is a path to the dataset that should
be de-identified. The input dataset is required to be in valid :abbr:`BIDS (Brain Imaging Data
Structure)` format.
We highly recommend that you validate your dataset before you run ``BIDSonym``
with the free, online `BIDS Validator <http://bids-standard.github.io/bids-validator/>`_.
However, the `BIDS Validator` is also run at the beginning of ``BIDSonym`` and will
you make you aware of possible problems and/or inconsistencies.
The exact command to run ``BIDSonym`` depends on the Installation method.
The common parts of the command follow the `BIDS-Apps
<https://github.com/BIDS-Apps>`_ definition.
Here's a very conceptual example: ::

    bidsonym data/bids_root/ analysis_level optional_arguments

However, it is important to note that ``BIDSonym`` is a special case of a ``BIDS-App``
in that it doesn't create a folder under the ``derivatives/`` directory within
which its outputs are written. As ``BIDSonym`` is intended to be run after
conversion (from e.g. ``DICOM``) but before any other processing step (e.g.,
quality control, preprocessing, etc.), the original files (non-defaced images
and complete JSON) will be moved to ``sourcedata/bidsonym`` and copied back to
the ``bids_root`` directory after de-indentification.
Based on this approach de-identified data will enter the processing stream, but
in case the defacing was not successful (too much or too little cut out) the
non-defaced images can be re-used, without the necessity to run the conversion again.

Command-Line Arguments
======================
.. argparse::
  :ref: bidsonym.run_deeid.get_parser
  :prog: bidsonym
  :nodefault:
  :nodefaultconst:

Example Call(s)
---------------

Below you'll find two examples calls that hopefully help
you to familiarize yourself with ``BIDSonym`` and its options.

Example 1
~~~~~~~~~

.. code-block:: bash

    bidsonym \
    /home/peer/bids/ \
    participant \
    --participant_label 01 \
    --deid pydeface \
    --brain_extraction bet \ 
    --bet_frac 0.5 \
    --del_meta 'InstitutionAddress' \

Here's what's in this call:

- The 1st positional argument is the BIDS directory (``/home/peer/bids``)
- The 2nd positional argument specifies whether we are running participant-
  or group-level mode. In more detail, if only a certain or all participants
  should be de-identified. You can choose between ``participant`` and ``group``.
  Here we choose ``participant``.
- The 3rd positional argument defines the ``subject id``, thus which specific
  participant should be de-identified. In this case, we choose ``01``.
- The 4th positional argument specifies which defacing algorithm should be run.
  You can choose between ``mri_deface``, ``pydeface``, ``quickshear`` and ``mridefacer``.
  In this example we choose ``pydeface``.
- The 5th positional argument specifies the algorithm that should be used for brain extraction
  (which will be used for quality control purposes). You have the options ``bet`` or ``nobrainer``.
  Here we chose ``bet``.
- The 6th position argument specifies the fractional intensity threshold used for ``bet``. 
  The value can range between ``0`` and ``1``, here we chose the default of 0.5. Please note,
  that this argument is only necessary when ``bet`` was chosen as brain extraction tool.
- The 7th argument indicates which metadata fields of the sidecar JSON file(s) should be deleted.
  This can be any of those included in the `BIDS specification <https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/01-magnetic-resonance-imaging-data.html>`_,
  if it exists in the JSON sidecar files of your ``BIDS dataset``.

Example 2
~~~~~~~~~

.. code-block:: bash

    bidsonym \
    /home/peer/bids/ \
    group \
    --deid mridefacer \
    --brain_extraction nobrainer \

Here's what's in this call:

- The 1st positional argument again is the BIDS directory (``/home/peer/bids``)
- The 2nd positional argument once more specifies whether we are running participant-
  or group-level mode. In more detail, if only a certain or all participants
  should be de-identified. You can choose between ``participant`` and ``group``.
  Here we choose ``group``. Hence, all participants will be de-identified and
  we don't need to specific a ``--participant_label`` as in Example 1.
- The 3rd positional argument specifies which defacing algorithm should be run.
  You can choose between ``mri_deface``, ``pydeface``, ``quickshear`` and ``mridefacer``.
  This time we choose ``mridefacer``.
- The 4th positional argument specifies the algorithm that should be used for brain extraction
  (which will be used for quality control purposes). You have the options ``bet`` or ``nobrainer``.
  Here we chose ``nobrainer``. 
- Contrary to Example 1, we don't delete any metadata field(s) of the sidecar JSON files.

Support and communication
=========================

The documentation of this project is found here: http://bidsonym.readthedocs.org/en/latest/.

All bugs, concerns and enhancement requests for this software can be submitted here:
https://github.com/peerherholz/bidsonym/issues.

If you have a problem or would like to ask a question about how to use ``BIDSonym``,
please submit a question to `NeuroStars.org <http://neurostars.org/tags/bidsonym>`_ with an ``bidsonym`` tag.
NeuroStars.org is a platform similar to StackOverflow but dedicated to neuroinformatics.

All previous ``BIDSonym`` questions are available here:
http://neurostars.org/tags/bidsonym/

To participate in the ``BIDSonym`` development-related discussions please use the
following mailing list: http://mail.python.org/mailman/listinfo/neuroimaging
Please add *[bidsonym]* to the subject line when posting on the mailing list.


Not running on a local machine? - Data transfer
===============================================

If you intend to run ``BIDSonym`` on a remote system, you will need to
make your data available within that system first.

Please contact you local system administrator regarding
possible and favourable transfer options (e.g., `rsync <https://rsync.samba.org/>`_
or `FileZilla <https://filezilla-project.org/>`_).

A very comprehensive approach would be `Datalad
<http://www.datalad.org/>`_, which will handle data transfers with the
appropriate settings and commands.
Datalad also performs version control over your data.
