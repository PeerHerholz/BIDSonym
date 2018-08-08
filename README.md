# BIDSonym

[![GitHub issues](https://img.shields.io/github/issues/PeerHerholz/BIDSonym.svg)](https://github.com/PeerHerholz/BIDSonym/issues/)
[![GitHub pull-requests](https://img.shields.io/github/issues-pr/PeerHerholz/BIDSonym.svg)](https://github.com/PeerHerholz/BIDSonym/pulls/)
[![GitHub contributors](https://img.shields.io/github/contributors/PeerHerholz/BIDSonym.svg)](https://GitHub.com/PeerHerholz/BIDSonym/graphs/contributors/)
[![GitHub Commits](https://github-basic-badges.herokuapp.com/commits/PeerHerholz/BIDSonym.svg)](https://github.com/PeerHerholz/BIDSonym/commits/master)
[![GitHub size](https://github-size-badge.herokuapp.com/PeerHerholz/BIDSonym.svg)](https://github.com/PeerHerholz/BIDSonym/archive/master.zip)
[![GitHub HitCount](http://hits.dwyl.io/PeerHerholz/BIDSonym.svg)](http://hits.dwyl.io/PeerHerholz/BIDSonym)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

## Description
:hocho: :hocho: A BIDS app for de-identification of neuroimaging data. Takes BIDS-format T1 and T2-weighted images and applies one of several popular de-identification algorithms. BIDSonym currently supports:
* [Pydeface](https://github.com/poldracklab/pydeface)
* [MRI deface](https://surfer.nmr.mgh.harvard.edu/fswiki/mri_deface)
* [Quickshear](https://github.com/nipy/quickshear)

**Using BIDSonym ensures that you can make collected neuroimaging data available for others without violating subjects' privacy or anonymity.**

## Documentation
Provide a link to the documention of your pipeline.

## How to report errors
Running into any bugs :beetle:? Check out the [open issues](https://github.com/PeerHerholz/BIDSonym/issues) to see if we're already working on it. If not, open up a new issue and we will check it out when we can!

## How to contribute
Thank you for considering contributing to our project! Before getting involved, please review our [Code of Conduct](https://github.com/PeerHerholz/BIDSonym/blob/master/CODE_OF_CONDUCT.md). Next, you can review  [open issues](https://github.com/PeerHerholz/BIDSonym/issues) that we are looking for help with. If you submit a new pull request please be as detailed as possible in your comments.

### Acknowledgements
Describe how would you would like users to acknowledge use of your App in their papers (citation, a paragraph that can be copy pasted, etc.)

### Usage
This App has the following command line arguments:

		usage: run.py [-h]
		              [--participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
		              bids_dir output_dir {participant,group}

		Example BIDS App entry point script.

		positional arguments:
		  bids_dir              The directory with the input dataset formatted
		                        according to the BIDS standard.
		  output_dir            The directory where the output files should be stored.
		                        If you are running a group level analysis, this folder
		                        should be prepopulated with the results of
		                        the participant level analysis.
		  {participant,group}   Level of the analysis that will be performed. Multiple
		                        participant level analyses can be run independently
		                        (in parallel).

		optional arguments:
		  -h, --help            show this help message and exit
		  --participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]
		                        The label(s) of the participant(s) that should be
		                        analyzed. The label corresponds to
		                        sub-<participant_label> from the BIDS spec (so it does
		                        not include "sub-"). If this parameter is not provided
		                        all subjects will be analyzed. Multiple participants
		                        can be specified with a space separated list.

To run it in participant level mode (for one participant):

    docker run -i --rm \
		-v /Users/filo/data/ds005:/bids_dataset:ro \
		-v /Users/filo/outputs:/outputs \
		bids/example \
		/bids_dataset /outputs participant --participant_label 01

After doing this for all subjects (potentially in parallel), the group level analysis
can be run:

    docker run -i --rm \
		-v /Users/filo/data/ds005:/bids_dataset:ro \
		-v /Users/filo/outputs:/outputs \
		bids/example \
		/bids_dataset /outputs group

### Special considerations
Describe whether your app has any special requirements. For example:

- Multiple map reduce steps (participant, group, participant2, group2 etc.)
- Unusual memory requirements
- etc.
