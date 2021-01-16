.. include:: links.rst

------------
Installation
------------

In general, there are two distinct ways to install and use ``BIDSonym``:
either through virtualization/container technology, that is `Docker`_ or
`Singularity`_, or in a `Bare metal version (Python 3.6+)`_.
Using local container method is highly recommended.
Once you are ready to run ```BIDSonym```, see `Usage <./usage.rst>`_ for details.

Docker
======

In order to run ```BIDSonym``` in a Docker container, Docker must be `installed
<https://docs.docker.com/engine/installation/>`_.
Once Docker is installed, you can get ``BIDSonym`` through running the following
command in the terminal of your choice:

.. code-block:: bash

    docker pull peerherholz/bidsonym:version

.. note::

   As of November 2020, `images older than 6 months will be deleted from Dockerhub
   <https://www.docker.com/pricing/retentionfaq>`_. As this is very problematic for everything
   reproducibility and version control, every version of the BIDSonym images are additionally
   uploaded on `OSF <https://osf.io/x4dku/>`_ and can be installed as outlined further below.

After the command finished (it may take a while depending on your internet connection),
you can run ``BIDSonym`` like this:

.. code-block:: bash

    $ docker run -ti --rm \
        -v path/to/your/bids_dataset:/bids_dataset:ro \
        peerherholz/bidsonym:latest \
        /bids_dataset \
        participant \
        --participant_label label \
        --deid defacing_algorithm \

Please have a look at the examples under Usage to get more information
about and familiarize yourself with ``BIDSonym``'s functionality.


Singularity
===========

For security reasons, many HPCs (e.g., TACC) do not allow Docker containers, but do
allow `Singularity <https://github.com/singularityware/singularity>`_ containers.

Directly pulling from Singularity Hub
----------------------------------------------------------
The ``BIDSonym`` Singularity image can directly be pulled from
Singularity Hub via:

    $ singularity pull PeerHerholz/BIDSonym

Preparing a Singularity image (Singularity version >= 2.5)
----------------------------------------------------------
If the version of Singularity on your HPC is modern enough you can create Singularity
image directly on the HCP.
This is as simple as: ::

    $ singularity build /my_images/bidsonym-<version>.simg docker://peerherholz/bidsonym:<version>

Where ``<version>`` should be replaced with the desired version of ``BIDSonym`` that you want to download.


Preparing a Singularity image (Singularity version < 2.5)
---------------------------------------------------------
In this case, start with a machine (e.g., your personal computer) with Docker installed.
Use `docker2singularity <https://github.com/singularityware/docker2singularity>`_ to
create a singularity image.
You will need an active internet connection and some time. ::

    $ docker run --privileged -t --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v D:\host\path\where\to\output\singularity\image:/output \
        singularityware/docker2singularity \
        peerherholz/bidsonym:<version>

Where ``<version>`` should be replaced with the desired version of ```BIDSonym``` that you want
to download.

Beware of the back slashes, expected for Windows systems.
For \*nix users the command translates as follows: ::

    $ docker run --privileged -t --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /absolute/path/to/output/folder:/output \
        singularityware/docker2singularity \
        peerherholz/bidsonym:<version>


Transfer the resulting Singularity image to the HPC, for example, using ``scp``. ::

    $ scp peerherholz_bidsonym*.simg user@hcpserver.edu:/my_images

Running a Singularity Image
---------------------------

If the data to be preprocessed is also on the HPC, you are ready to run bidsonym. ::

    $ singularity run --cleanenv /my_images/peerherholz_bidsonym*.simg \
        path/to/your/bids_dataset \
        participant \
        --participant-label label \
        --deid defacing_algorithm

.. note::

   Singularity by default `exposes all environment variables from the host inside
   the container <https://github.com/singularityware/singularity/issues/445>`_.
   Because of this your host libraries (such as nipype) could be accidentally used
   instead of the ones inside the container - if they are included in ``PYTHONPATH``.
   To avoid such situation we recommend using the ``--cleanenv`` singularity flag
   in production use. For example: ::

    $ singularity run --cleanenv /my_images/peerherholz_bidsonym*.simg \
        path/to/your/bids_dataset \
        participant \
        --participant-label label \
        --deid defacing_algorithm


   or, unset the ``PYTHONPATH`` variable before running: ::

    $ unset PYTHONPATH; singularity /my_images/peerherholz_bidsonym*.simg \
        path/to/your/bids_dataset \
        participant \
        --participant-label label \
        --deid defacing_algorithm


.. note::

   Depending on how Singularity is configured on your cluster it might or might not
   automatically bind (mount or expose) host folders to the container.
   If this is not done automatically you will need to bind the necessary folders using
   the ``-B <host_folder>:<container_folder>`` Singularity argument.
   For example: ::

    $ singularity run --cleanenv -B path/to/bids_dataset/on_host:/bids_dataset \
        /my_images/peerherholz_bidsonym*.simg \
        bids_dataset \
        participant \
        --participant-label label \
        --deid defacing_algorithm

Bare metal version (Python 3.6+)
===========================================

.. warning::

   This method is not recommended! Make sure you would rather do this than
   use a `Docker`_ or a `Singularity`_.

Make sure all of ``BIDSonym``'s `External Dependencies`_ are installed.
These tools must be installed and their binaries available in the
system's ``$PATH``.
A relatively interpretable description of how your environment can be set-up
is found in the `Dockerfile <https://github.com/peerherholz/bidsonym/blob/master/Dockerfile>`_.

On a functional Python 3.6 (or above) environment with ``pip`` installed,
```BIDSonym``` can be installed using the habitual command ::

    $ pip install bidsonym

Check your installation with the ``--version`` argument ::

    $ bidsonym --version


External Dependencies
---------------------

``BIDSonym`` is written using Python 3.6 (or above).
It requires some other neuroimaging software tools that are
not handled by the Python's packaging system (Pypi) used to deploy
the ``BIDSonym`` package:

- FSL_ (version 5.0.9)
- `MRI_deface <https://surfer.nmr.mgh.harvard.edu/fswiki/mri_deface>`_
- `Quickshear <https://github.com/nipy/quickshear>`_
- `mridefacer <https://github.com/mih/mridefacer>`_
- `bids-validator <https://github.com/bids-standard/bids-validator>`_ (version 1.2.3)

Previous image versions on OSF
------------------------------

As mentioned above, Dockerhub introduced the deletion of images older than 6 months.
Thus all previous versions of the ``BIDSonym`` ``Docker`` image can be found on `OSF <https://osf.io/x4dku/>`_.
After downloading and unzipping your desired version, images be made available and ready to run via:

    $ docker import bidsonym_version_vX.Y.Z.tar

where ``XYZ`` is the version you downloaded.
