===============================
BIDSonym
===============================

.. image:: https://img.shields.io/travis/PeerHerholz/BIDSonym.svg
        :target: https://travis-ci.org/PeerHerholz/BIDSonym

.. image:: https://img.shields.io/github/issues-pr/PeerHerholz/BIDSonym.svg
    :alt: PRs
    :target: https://github.com/PeerHerholz/BIDSonym/pulls/

.. image:: https://img.shields.io/github/contributors/PeerHerholz/BIDSonym.svg
    :alt: Contributors
    :target: https://GitHub.com/PeerHerholz/BIDSonym/graphs/contributors/

.. image:: https://github-basic-badges.herokuapp.com/commits/PeerHerholz/BIDSonym.svg
    :alt: Commits
    :target: https://github.com/PeerHerholz/BIDSonym/commits/master

.. image:: http://hits.dwyl.io/PeerHerholz/BIDSonym.svg
    :alt: Hits
    :target: http://hits.dwyl.io/PeerHerholz/BIDSonym

.. image:: https://img.shields.io/docker/cloud/automated/peerherholz/bidsonym
    :alt: Dockerbuild
    :target: https://cloud.docker.com/u/peerherholz/repository/docker/peerherholz/bidsonym

.. image:: https://img.shields.io/docker/pulls/peerherholz/bidsonym
    :alt: Dockerpulls
    :target: https://cloud.docker.com/u/peerherholz/repository/docker/peerherholz/bidsonym
    
.. image:: https://www.singularity-hub.org/static/img/hosted-singularity--hub-%23e32929.svg
    :alt: SingularityHub
    :target: https://singularity-hub.org/collections/4645

.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
    :alt: License
    :target: https://opensource.org/licenses/BSD-3-Clause

.. image:: https://upload.wikimedia.org/wikipedia/commons/7/74/Zotero_logo.svg
    :alt: Zotero
    :target: https://www.zotero.org/groups/2362367/bidsonym

.. image:: https://img.shields.io/badge/Supported%20by-%20CONP%2FPCNO-red
    :alt: support_conp
    :target: https://conp.ca/

Description
===========
A `BIDS <https://bids-specification.readthedocs.io/en/stable/>`_ `App <https://bids-apps.neuroimaging.io/>`_ for the de-identification of neuroimaging data. ``BIDSonym`` gathers all T1w images from a BIDS dataset and applies one of several popular de-identification algorithms. It currently supports:

`MRI deface <https://surfer.nmr.mgh.harvard.edu/fswiki/mri_deface>`_, `Pydeface <https://github.com/poldracklab/pydeface>`_, `Quickshear <https://github.com/nipy/quickshear>`_ and `mridefacer <https://github.com/mih/mridefacer>`_.

.. image:: https://raw.githubusercontent.com/PeerHerholz/BIDSonym/master/img/bidsonym_example.png
   :alt: alternate text

Additionally, the user can choose to evaluate the sidecar JSON files regarding potentially sensitive information,
like for example participant names and define a list of fields which information should be deleted.

**Using BIDSonym can help you can make collected neuroimaging data available for others without violating subjects' privacy or anonymity (depending on the regulations of the country you're in).**

.. intro-marker

Usage
=====

.. usage-marker

This App has the following command line arguments:

usage:	run.py [-h]

[--participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]

[--deid {pydeface,mri_deface,quickshear}]

[--del_nodeface {del,no_del}]

[--deface_t2w]

[--check_meta]

[--del_meta META_DATA_FIELD [META_DATA_FIELD ...]]

[--brainextraction {bet,nobrainer}]

[--bet_frac BET_FRAC]

bids_dir {participant,group}

a BIDS app for de-identification of neuroimaging data

positional arguments:
  bids_dir              The directory with the input dataset formatted
			according to the BIDS standard.
  output_dir            The directory where the not de-identified raw files should be stored,
			in case you decide to keep them.
  {participant,group}   Level of the analysis that will be performed. Multiple
			participant level analyses can be run independently
			(in parallel) using the same output_dir.

optional arguments:
  --participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]
			The label(s) of the participant(s) that should be
			analyzed. The label corresponds to
			sub-<participant_label> from the BIDS spec (so it does
			not include "sub-"). If this parameter is not provided
			all subjects should be analyzed. Multiple participants
			can be specified with a space separated list.
  --deid {pydeface,mri_deface,quickshear}
			Approach to use for de-identifictation.
  --deface_t2w \
            Deface T2w images by using defaced T1w image as deface-mask.
  --check_meta META_DATA_FIELD [META_DATA_FIELD ...]  
            Indicate which information from the image and
            :code:`.json` meta-data files should be check for potentially problematic information. 
            Indicate strings that should be searched for.
            The results will be saved to :code:`sourcedata/`.
  --del_meta META_DATA_FIELD [META_DATA_FIELD ...]
			Indicate (via strings) if and which information from the :code:`.json` meta-data
			files should be deleted. If so, the original :code:`.json` files
			will be copied to :code:`sourcedata/`.
  --brainextraction {BET, no_brainer}
			What algorithm should be used for pre-defacing brain extraction
			(outputs will be used in quality control).
  --bet_frac [BET_FRAC]
			In case BET is used for pre-defacing brain extraction, provide a Frac value.
  --skip_bids_validation \
            Assume the input dataset is BIDS compliant and skip the validation (default: False).
  -v \
    BIDS-App version.


Run it in participant level mode (for one participant):

.. code-block::

	docker run -i --rm \
		    -v /Users/peer/ds005:/bids_dataset \
	            peerherholz/bidsonym \
		    /bids_dataset \
		    participant --deid pydeface --del_meta 'InstitutionAddress' \
		    --participant_label 01
		    --brainextraction bet --bet_frac 0.5


Run it in group level mode (for all participants):

.. code-block::

	docker run -i --rm \
		   -v /Users/peer/ds005:/bids_dataset \
		   peerherholz/bidsonym \
		   /bids_dataset  group --deid pydeface --del_meta 'InstitutionAddress' \
		   --brainextraction bet --bet_frac 0.5

.. usage-marker-end


Installation
============
Following the `BIDS apps standard <https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005209>`_ it is recommend to install and use BIDSonym in its Docker or Singularity form. \
To get the BIDSonym Docker image, you need to `install docker <https://docs.docker.com/install/>`_ and within the terminal of your choice type:

:code:`docker pull peerherholz/bidsonym`

To get its Singularity version, you need to `install singularity <https://singularity.lbl.gov/all-releases>`_ and within the terminal of your choice type:

:code:`singularity pull PeerHerholz/BIDSonym`

Documentation
=============
BIDSonym's documentation can be found `here <https://peerherholz.github.io/BIDSonym/>`_.


How to report errors
====================
Running into any bugs :beetle:? Check out the `open issues <https://github.com/PeerHerholz/BIDSonym/issues>`_ to see if we're already working on it. If not, open up a new issue and we will check it out when we can!

How to contribute
=================
Thank you for considering contributing to our project! Before getting involved, please review our `Code of Conduct <https://github.com/PeerHerholz/BIDSonym/blob/master/CODE_OF_CONDUCT.rst>`_. Next, you can review `open issues <https://github.com/PeerHerholz/BIDSonym/issues>`_ that we are looking for help with. If you submit a new pull request please be as detailed as possible in your comments. Please also have a look at our `contribution guidelines <https://github.com/PeerHerholz/BIDSonym/blob/master/CONTRIBUTING.rst>`_.

Acknowledgements
================
Please acknowledge this work by mentioning explicitly the name of this software
(*BIDSonym*) and the version, along with a link to the `GitHub repository
<https://github.com/peerherholz/bidsonym>`_ or the Zenodo reference.
For more details, please see `citation <https://peerherholz.github.io/BIDSonym/citing.html>`_.

Support
=======
This work is supported in part by funding provided by `Brain Canada <https://braincanada.ca/>`_, in partnership with `Health Canada <https://www.canada.ca/en/health-canada.html>`_, for the `Canadian Open Neuroscience Platform initiative <https://conp.ca/>`_.

.. image:: https://conp.ca/wp-content/uploads/elementor/thumbs/logo-2-o5e91uhlc138896v1b03o2dg8nwvxyv3pssdrkjv5a.png
    :alt: logo_conp
    :target: https://conp.ca/

Furthermore, the project is supported by [Repronim](https://www.repronim.org/) under NIH-NIBIB P41 EB019936. 