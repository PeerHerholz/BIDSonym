# BIDSonym

[![GitHub issues](https://img.shields.io/github/issues/PeerHerholz/BIDSonym.svg)](https://github.com/PeerHerholz/BIDSonym/issues/)
[![GitHub pull-requests](https://img.shields.io/github/issues-pr/PeerHerholz/BIDSonym.svg)](https://github.com/PeerHerholz/BIDSonym/pulls/)
[![GitHub contributors](https://img.shields.io/github/contributors/PeerHerholz/BIDSonym.svg)](https://GitHub.com/PeerHerholz/BIDSonym/graphs/contributors/)
[![GitHub Commits](https://github-basic-badges.herokuapp.com/commits/PeerHerholz/BIDSonym.svg)](https://github.com/PeerHerholz/BIDSonym/commits/master)
[![GitHub size](https://github-size-badge.herokuapp.com/PeerHerholz/BIDSonym.svg)](https://github.com/PeerHerholz/BIDSonym/archive/master.zip)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/Django.svg)](https://pypi.python.org/pypi/ansicolortags/)
[![GitHub HitCount](http://hits.dwyl.io/PeerHerholz/BIDSonym.svg)](http://hits.dwyl.io/PeerHerholz/BIDSonym)
[![Docker Hub](https://img.shields.io/docker/pulls/peerherholz/bidsonym.svg?maxAge=2592000)](https://hub.docker.com/r/peerherholz/bidsonym/)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
<a href="https://osf.io/x4dku/">
<img border="0" alt="W3Schools" src="https://cdn.cos.io/media/images/osf-logo-black.original.png" width="80" height="20">

## Description
:hocho: :hocho: A BIDS app for de-identification of neuroimaging data. Takes BIDS-format T1 and T2-weighted images and applies one of several popular de-identification algorithms. BIDSonym currently supports:
* [Pydeface](https://github.com/poldracklab/pydeface)
* [MRI deface](https://surfer.nmr.mgh.harvard.edu/fswiki/mri_deface)
* [Quickshear](https://github.com/nipy/quickshear)

<img src="https://github.com/PeerHerholz/BIDSonym/blob/master/img/bidsyonym_example.png" alt="bidsonym example" width="800" height="250" border="100">

**Using BIDSonym ensures that you can make collected neuroimaging data available for others without violating subjects' privacy or anonymity.**

## Documentation
Provide a link to the documention of your pipeline.

## How to report errors
Running into any bugs :beetle:? Check out the [open issues](https://github.com/PeerHerholz/BIDSonym/issues) to see if we're already working on it. If not, open up a new issue and we will check it out when we can!

## How to contribute
Thank you for considering contributing to our project! Before getting involved, please review our [Code of Conduct](https://github.com/PeerHerholz/BIDSonym/blob/master/CODE_OF_CONDUCT.md). Next, you can review  [open issues](https://github.com/PeerHerholz/BIDSonym/issues) that we are looking for help with. If you submit a new pull request please be as detailed as possible in your comments. Please also have a look at our [contribution guidelines](https://github.com/PeerHerholz/BIDSonym/blob/master/CONTRIBUTING.md).

### Acknowledgements
Describe how would you would like users to acknowledge use of your App in their papers (citation, a paragraph that can be copy pasted, etc.)

### Usage
This App has the following command line arguments:

	usage: run.py [-h]
	              [--participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
	              [--deid {pydeface,mri_deface,quickshear}]
	              [--del_nodeface {del,no_del}]
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
	  -h, --help            show this help message and exit
	  --participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]
	                        The label(s) of the participant(s) that should be
	                        analyzed. The label corresponds to
	                        sub-<participant_label> from the BIDS spec (so it does
	                        not include "sub-"). If this parameter is not provided
	                        all subjects should be analyzed. Multiple participants
	                        can be specified with a space separated list.
	  --deid {pydeface,mri_deface,quickshear}
	                        Approach to use for de-identifictation.
	  --del_nodeface {del,no_del}
	                        Overwrite and delete original data or copy original
	                        data to different folder.


To run it in participant level mode (for one participant):

    docker run -i --rm \
		-v /Users/filo/data/ds005:/bids_dataset \
		bids/bidsonym \
		/bids_dataset participant --deid pydeface --del_nodeface no_del --participant_label 01

After doing this for all subjects (potentially in parallel), the group level analysis
can be run:

    docker run -i --rm \
		-v /Users/filo/data/ds005:/bids_dataset \
		bids/bidsonym \
		/bids_dataset  group --deid pydeface --del_nodeface no_del
