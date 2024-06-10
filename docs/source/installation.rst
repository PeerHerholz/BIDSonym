.. include:: links.rst

------------
Installation
------------

In general, there are two distinct ways to install and use ``BIDSonym``:
either through virtualization/container technology, that is `Docker`_ or
`Singularity`_, or in a `Bare metal version (Python 3.6+)`_.
Using a container method is highly recommended as they entail entire operating systems through kernel level virtualization and
thus include all software necessary to run ``BIDSonym``, while at the same time presenting a lightweight alternative to virtual machines.
Once you are ready to run ``BIDSonym``, see `Usage <./usage.rst>`_ for details.

Docker
======

In order to run ```BIDSonym``` in a Docker container, Docker must be `installed
<https://docs.docker.com/engine/installation/>`_ on your system.
Once Docker is installed, you can get ``BIDSonym`` through running the following
command in the terminal of your choice:

.. code-block:: bash

    docker pull peerherholz/bidsonym:version

Where ``version`` is the specific version of ``BIDSonym`` you would like to use. For example, if you want 
to employ the ``latest``/most up to date ``version`` you can either run 

.. code-block:: bash

    docker pull peerherholz/bidsonym:latest

or the same command without the ``:latest`` tag, as ``Docker`` searches for the ``latest`` tag by default.
However, as the ``latest`` version is subject to changes and not necessarily in synch with the most recent ``numbered version``, it 
is recommend to utilize the latter to ensure reproducibility. For example, if you want to employ ``BIDSonym v0.0.4`` the command would look as follows:

.. code-block:: bash

    docker pull peerherholz/bidsonym:v0.0.4

.. note::

   As of November 2020, `images older than 6 months will be deleted from Dockerhub
   <https://www.docker.com/pricing/retentionfaq>`_. As this is very problematic for everything
   reproducibility and version control, every version of the ``BIDSonym images`` are additionally
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

Please have a look at the examples under `Usage <./usage.rst>`_ to get more information
about and familiarize yourself with ``BIDSonym``'s functionality.


Singularity
===========

For security reasons, many HPCs (e.g., TACC) do not allow Docker containers, but support
allow `Singularity <https://github.com/singularityware/singularity>`_ containers. Depending
on the ``Singularity`` version available to you, there are two options to get ``BIDSonym`` as
a ``Singularity image``.

Preparing a Singularity image (Singularity version >= 2.5)
----------------------------------------------------------
If the version of Singularity on your HPC is modern enough you can create a ``Singularity
image`` directly on the HCP.
This is as simple as: 

.. code-block:: bash

    $ singularity build /my_images/bidsonym-<version>.simg docker://peerherholz/bidsonym:<version>

Where ``<version>`` should be replaced with the desired version of ``BIDSonym`` that you want to download.
For example, if you want to use ``BIDSonym v0.0.4``, the command would look as follows.

.. code-block:: bash

    $ singularity build /my_images/bidsonym-v0.0.4.simg docker://peerherholz/bidsonym:v0.0.4


Preparing a Singularity image (Singularity version < 2.5)
---------------------------------------------------------
In this case, start with a machine (e.g., your personal computer) with ``Docker`` installed and
the use `docker2singularity <https://github.com/singularityware/docker2singularity>`_ to
create a ``Singularity image``. You will need an active internet connection and some time. 

.. code-block:: bash

    $ docker run --privileged -t --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /absolute/path/to/output/folder:/output \
        singularityware/docker2singularity \
        peerherholz/bidsonym:<version>

Where ``<version>`` should be replaced with the desired version of ```BIDSonym``` that you want
to download and ``/absolute/path/to/output/folder`` with the absolute path where the created ``Singularity image``
should be stored. Sticking with the example of ``BIDSonym v0.0.4`` this would look as follows:

.. code-block:: bash

    $ docker run --privileged -t --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /absolute/path/to/output/folder:/output \
        singularityware/docker2singularity \
        peerherholz/bidsonym:v0.0.4

Beware of the back slashes, expected for Windows systems. The above command would translate to Windows systems as follows:

.. code-block:: bash

    $ docker run --privileged -t --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v D:\host\path\where\to\output\singularity\image:/output \
        singularityware/docker2singularity \
        peerherholz/bidsonym:<version>


You can then transfer the resulting ``Singularity image`` to the HPC, for example, using ``scp``. ::

    $ scp peerherholz_bidsonym<version>.simg <user>@<hcpserver.edu>:/my_images

Where ``<version>`` should be replaced with the version of ```BIDSonym``` that you used to create the ``Singularity image``, ``<user>``
with your ``user name`` on the HPC and ``<hcpserver.edu>`` with the address of the HPC.  

Running a Singularity Image
---------------------------

If the data to be preprocessed is also on the HPC, you are ready to run bidsonym. 

.. code-block:: bash

    $ singularity run --cleanenv /my_images/bidsonym-<version>.simg \
        path/to/your/bids_dataset \
        participant \
        --participant-label label \
        --deid defacing_algorithm

.. note::

    Make sure to check the name of the created ``Singularity image`` as that might
    diverge based on the method you used. Here and going forward it is assumed that you used ``Singularity >= 2.5``
    and thus ``bidsonym-<version>.simg`` instead of ``peerherholz_bidsonym<version>.simg``.   


.. note::

   Singularity by default `exposes all environment variables from the host inside
   the container <https://github.com/singularityware/singularity/issues/445>`_.
   Because of this your host libraries (such as nipype) could be accidentally used
   instead of the ones inside the container - if they are included in ``PYTHONPATH``.
   To avoid such situation we recommend using the ``--cleanenv`` singularity flag
   in production use. For example: ::

    $ singularity run --cleanenv /my_images/bidsonym-<version>.simg \
        path/to/your/bids_dataset \
        participant \
        --participant-label label \
        --deid defacing_algorithm


   or, unset the ``PYTHONPATH`` variable before running: ::

    $ unset PYTHONPATH; singularity /my_images/bidsonym-<version>.simg \
        path/to/your/bids_dataset \
        participant \
        --participant-label label \
        --deid defacing_algorithm


.. note::

   Depending on how ``Singularity`` is configured on your cluster it might or might not
   automatically ``bind`` (``mount`` or ``expose``) ``host folders`` to the container.
   If this is not done automatically you will need to ``bind`` the necessary folders using
   the ``-B <host_folder>:<container_folder>`` ``Singularity`` argument.
   For example: ::

    $ singularity run --cleanenv -B path/to/bids_dataset/on_host:/bids_dataset \
        /my_images/bidsonym-<version>.simg \
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
``BIDSonym`` can be installed using the habitual command:

.. code-block:: bash

    $ pip install bidsonym

Check your installation with the ``--version`` argument:

.. code-block:: bash

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

.. code-block:: bash

    $ docker import bidsonym_version_vX.Y.Z.tar

where ``XYZ`` is the version you downloaded, for example assuming ``BIDSonym v0.0.4``:

.. code-block:: bash

    $ docker import bidsonym_version_v0.0.4.tar

