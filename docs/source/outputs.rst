.. _outputs:

.. include:: links.rst

-------------------
Outputs of BIDSonym
-------------------

BIDSonym generates three broad classes of outcomes:

  1. **Visual QA (quality assessment)**:
     one graphic showing the overlay between the outcome of brain extraction and defaced images per image 
     and one gif per defaced image per subject, that allows the user a visual assessment of the quality
     of de-identification and ensures the transparency of ``BIDSonym``'s operation.

  2. **imaging data** including defaced images in the `BIDS root` directory and
     non-defaced images in the `sourcedata/bidsonym` directory.

  3. **sidecar JSON and metadata .tsv files** including de-identified files in the `BIDS root`
     directory and not de-identified files in the `sourcedata/bidsonym` directory.


Visual QA
--------------

``BIDSonym`` related graphical outputs, written to ``sourcedata/bidsonym/sub-<subject_label>/(ses-<session_label>)``.
These graphics provide a quick way to make a visual inspection of the de-identification easy.
Within static graphics, each displays the whole ``defaced image`` in 10 slices along different
directions (x,y,z). To evaluate if the ``defacing`` was too stringent, a ``brainmask`` created before
the ``defacing`` is overlaid. The graphics additionally include a gif within which the ``defaced image`` is scrolled
through each direction. 

Imaging data
------------

Regarding ``Imaging data`` two types of outputs will be created when running ``BIDSonym``:

copied non-defaced images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The non-defaced images that enter ``BIDSonym`` as input will be copied
to ``sourcedata/bidsonym/sub-<subject_label>/`` and provide with a ``no_deid``
identifier in their filename. For example:
``bids_dataset/sub-<subject_label>/anat/sub-<subject_label>_T1w.nii.gz``
will be copied and renamed to
``bids_dataset/sourcedata/bidsonym/sub-<subject_label>/sub-<subject_label>_T1w_no_deid.nii.gz``.
This step is intended to keep the ``non-defaced images`` in case the defacing did not succeed (for
example too much or too little information cut out), so that users can copy the non-defaced images
back to the ``bids_dataset`` directory and do not need to convert the non-defaced images from ``DICOM``
again.


`and`


defaced images
~~~~~~~~~~~~~~

The images of either a specified participant or the whole group (depending on the ``analysis_level parameter``, please see `Usage <./usage.rst>`_)
in the ``bids_dataset`` will be defaced via the specified defacing algorithm (please see `Usage <./usage.rst>`_).
Neither the data structure nor the filenames will be changed. For example:
``bids_dataset/sub-<subject_label>/anat/sub-<subject_label>_T1w.nii.gz`` will be defaced, overwriting
the input image, so that the ``bids_dataset`` directory contains only de-identified data which then
can be entered into a processing pipeline and/or publicly shared (once again, depending on the regulations
of the country you're in and/or acquired the data in).




Sidecar JSON and metadata .tsv files
------------------------------------

Regarding ``Sidecar JSON and metadata .tsv files`` three types of outputs will be created when running ``BIDSonym``:


metadata .tsv files
~~~~~~~~~~~~~~~~~~~

``BIDSonym`` will access both the information stored in the ``header`` of the images and ``sidecar JSON files``, writing them
to ``.tsv`` files with two columns: 1. the type of information and 2. if it might be problematic in terms of data sharing. By default,
the ``descrip`` field is considered to be problematic in the ``header`` and the following in the ``sidecar JSON files``: ``AcquisitionTime``, 
``InstitutionAddress``, ``InstitutionName``, ``InstitutionalDepartmentName``, ``ProcedureStepDescription``, ``ProtocolName``, 
``PulseSequenceDetails``, ``SeriesDescription`` and ``global``. However, the user can provide a list of strings for which will be 
searched in the extracted information via the ``--check_meta_data`` argument. For the defaults and if a certain string, e.g., ``name`` or ``location`` is found, the 
respective field is marked as ``maybe`` in the ``problematic`` column. Thus users can investigate and evaluate if potentially 
sensitive information is present in the data and, if not done already, indicate metadata fields which information should be 
deleted through the ``--del_meta`` argument. However, only metadata from the ``sidecar JSON files`` but not the ``image headers`` will be deleted.


copied non-de-identified sidecar JSON files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comparable to the ``non-defaced images``, the ``non-de-identified
sidecar JSON files`` will be copied to ``sourcedata/bidsonym/sub-<subject_label>/``
and provided with a ``no-deid`` identifier. Here's an example:
``bids_dataset/sub-<subject_label>/anat/sub-<subject_label>_T1w.json``
will be copied and renamed to
``bids_dataset/sourcedata/sub-<subject_label>/anat/sub-<subject_label>_T1w_no_deid.json``.
This step is intended to keep the ``non-de-identified
sidecar JSON files`` in case the de-identification did not succeed , so that users can copy
the ``non-de-identified sidecar JSON files``
back to the ``bids_dataset`` directory and do not need to do run the conversion again.
Please not that while de-facing only targets ``structural data``, the ``sidecar JSON files``
of all modalities will be included.


de-identified sidecar JSON files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If set by the user through the ``--del_meta`` argument, ``BIDSonym`` will deleted
the value of indicated ``metadata fields`` in the ``sidecar JSON files`` within the
``bids_dataset`` directory, replacing them with the string ``deleted_by_bidsonym``.
For example, if the ``metadata field`` ``InstitutionAddress`` should be deleted,
the respective value of the ``sidecar JSON files`` will change from e.g.,
``InstitutionAddress : 'A restaurant at the end of the Universe.'``  to
``InstitutionAddress : 'deleted_by_bidsonym'``.
