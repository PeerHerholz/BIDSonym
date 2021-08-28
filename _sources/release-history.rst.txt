===============
Release History
===============
v0.0.5 (2021-08-28)
===================

This release includes a variety of bug fixes and `JOSS review process <https://github.com/openjournals/joss-reviews/issues/3169>`_. 
Concerning bug fixes an `argument swap in the copy_no_deid function was corrected <https://github.com/PeerHerholz/BIDSonym/commit/177f447753ad72df8ac37440017d23903c6a0b8e>`_,
plotting functions were adapted (`wrt T2w defacing <https://github.com/PeerHerholz/BIDSonym/commit/08a233db148c2260cad82b4a78b8acf9f930b3aa>`_ and 
`main plotting function <https://github.com/PeerHerholz/BIDSonym/commit/4ca3ed985e5b6aed5f164a2f40c9948c6782a595>`_) and `mridefacer problems solved <https://github.com/PeerHerholz/BIDSonym/commit/5ddcc4281b39f2b1db9d872138df965553f1ab4d>`_.
Regarding the `JOSS review process <https://github.com/openjournals/joss-reviews/issues/3169>`_, multiple sections of the documentation were extended and several typos were fixed. A new section displaying 
`an usage example <https://github.com/PeerHerholz/BIDSonym/commit/bdd683f3434cf96e656b7a41372d3750b30d3804>`_ was added to help interested users and allow software testing. As this uses `an open non-deidentified dataset <https://openneuro.org/datasets/ds000031/versions/00001>`_,
the `example data was removed <https://github.com/PeerHerholz/BIDSonym/commit/732f290f277c21c07f7a8d3085f1543565d23801>`_. Additionally, the ``Singularity image`` was `dropped <https://github.com/PeerHerholz/BIDSonym/commit/573011c595507fb18210a87cd3afc87b34dda812>`_ due to recent developments around ``Singularity hub`` and adapted to suggest obtaining a ``Singularity image`` through a direct download from ``Dockerhub``.

v0.0.4 (2021-01-16)
===================

This version adds bidsonym to PyPi.

v0.0.3 (2021-01-16)
===================

This release mainly consists of various bug fixes and minor new features. 
Bug fixes mainly addressed problems related to how sessions and corresponding were handled. 
New features in particular refer to reorganizing the outcomes into data (and if present session) 
specific directories and stable graphics generation.  

v0.0.2 (2020-08-12)
===================

Initial release draft to enable further work on versioning.

v0.0.1 (2020-08-12)
===================

Initial release draft to enable further work on versioning.