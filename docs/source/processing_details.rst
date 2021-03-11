.. include:: links.rst

------------------
Processing details
------------------

    .. image:: https://raw.githubusercontent.com/PeerHerholz/BIDSonym/master/docs/source/_static/bidsonym_functionality.png
       :alt: alternate text


When running ``BIDSonym``, the following processing steps are executed:

  1. **running BIDS-validator**:

    Before anything else happens, the `BIDS-validator <https://github.com/bids-standard/bids-validator>`_  
    is run in order to evaluate if the provided `bids_dataset` is valid with regard to the `BIDS specification <https://bids-specification.readthedocs.io/en/stable/>`_.
    If that's the case, `BIDSonym` will continue with the subsequent steps, if not, it will stop and provide
    the user with a message of why the `bids_dataset` was evaluated as `not valid`.
    Users should then conduct the changes necessary to make it valid, as otherwise `BIDSonym` won't run.
    This step and its implementation is based on and borrowed from the respective
    `fmriprep <https://github.com/poldracklab/fmriprep/blob/a774bb55efb6163e9ad860e6a0be0e4cfa426745/fmriprep/utils/bids.py#L64>`_
    functionality, thus all credits go to their amazing developer team. The same accounts for the copyright. Below you see an example
    of the ``BIDS-validator`` output, providing information about the ``bids_dataset`` and a warning telling you that the ``README``
    is missing.

    .. image:: https://raw.githubusercontent.com/PeerHerholz/BIDSonym/master/docs/source/_static/bidsvalidator_example.png
       :alt: alternate text


    2. **brain extraction applied to non-defaced images**:

    In order to evaluate the success of the de-facing, especially with regard to "cut out too much",
    a brain extraction/skull stripping procedure will be applied to the images before the de-facing.
    The respective brain mask will be overlaid on the de-faced images within the visual QA report to
    allow an easy assessment of potentially too stringent outcomes. A respective example is shown below
    where the upper panel displays a non-defaced image and the lower one a defaced image. The reddish overlay
    represents a brain mask that was extracted before the image was defaced.

    .. image:: https://raw.githubusercontent.com/PeerHerholz/BIDSonym/master/docs/source/_static/brainext_defacing.png
       :alt: alternate text

  3. **moving of non-de-identified data**:

    The non-de-identified data, that is ``structural images`` and ``sidecar JSON files``, will be moved from the
    ``bids_dataset`` directory to ``bids_dataset/sourcedata/bidsonym``. In case the de-identification was not
    successful (too much or too little information deleted), the non-de-identified version can easily be copied
    back from to the ``bids_dataset`` directory without the necessity to run the corresponding DICOM to Nifti in
    BIDS conversion again.

  4. **evalution of metadata**:

    The metadata found in both, the ``header of the images`` and ``sidecar JSON files`` will gathered
    and saved in a tabular data file (.tsv) of the form ``metadata field : value`` to the
    ``bids_dataset/sourcedata/bidsonym/`` directory. Additionally, a third column ``problematic`` will
    indicate if the ``value`` of a certain ``metadata field`` is potentially problematic or sensitive.
    By default all values will considered not problematic (``no``). Only if the user specifies a list
    of strings which might be included in problematic or sensitive information (e.g., 'name') ``BIDSonym``
    will search for these strings and mark respective ``values`` of ``metadata fields`` as problematic (``yes``)

  5. **defacing of images**:

    Subsequently, the chosen defacing algorithm will be applied to the ``structural images``, aiming to remove
    features that could potentially allow or aid the identification of participants' identity (e.g., their face).
    Depending on the algorithm chosen, more or less features are removed and the sufficiency needs to be evaluated
    by the user (supported through the visual QA). If the ``-deface_t2w`` flag is set, ``structural T2 weighted
    images`` will de-faced by using the respective ``de-faced T1 weighted image`` of the same subject as a mask.
    All de-faced images will be written to the ``bids_dataset`` directory.
    
  6. **de-indetification of metadata fields**:

    If indicated by the user via a list of strings, the ``values`` of certain ``metadata fields`` will be replaced by
    the string ``deleted_by_bidsonym``. As the image files, metadata files will be moved to
    ``bids_dataset/sourcedata/bidsonym/`` and de-identified files will be written to ``bids_dataset``.

  7. **renaming of original files**:

    All files, including imaging and metadata, that are stored under  ``bids_dataset/sourcedata/bidsonym/`` will be
    renamed to indicate their respective status. Thus the descriptor `_desc-nondeid` is added to the respective
    file names.
