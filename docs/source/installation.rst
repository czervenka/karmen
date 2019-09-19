############################################
Installation
############################################

Making your printer Karmen-ready
--------------------------------

.. note::
  There might be other viable solutions, but at the moment, Karmen supports only
  Octoprint.

The de-facto standard for making your 3D printer accessible over the network
is `Octoprint <https://octoprint.org>`_. Its installation can be greatly
simplified by using a Raspbian-derived image with a pre-configured installation
called `OctoPi <https://github.com/guysoft/OctoPi>`_ that is designed for Raspberry Pi
microcomputers.

After the initial Octoprint/OctoPi setup that connects your printer is performed,
you are ready to connect the printer to Karmen. Please note, that any issues you
might have with a webcam stream or other specifics, are related to Octoprint/OctoPi
and not to Karmen. *Karmen is only using Octoprint's API to communicate with the
printer.*

Also, make sure that the Octoprint instance is accessible over the same network
on which Karmen will be running.

.. warning::
  Karmen currently does not support the secured Octoprint installations, it relies
  on the publicly available API. We are working on it. Do not expose your unsecured
  printer to the internet.

Installing Karmen
-----------------

Karmen should run on any Linux-based distribution, and we recommend to use a standalone
computer for it. A Raspberry Pi is again a good fit. The only dependency Karmen requires
is `Docker <https://www.docker.com>`_ easily installed on Raspberry Pi by running the
following commands as described on `Docker blog <https://blog.docker.com/2019/03/happy-pi-day-docker-raspberry-pi/>`_.
We recommend to use a clean Raspbian image for installing Karmen.

.. code-block:: sh

   sudo apt-get install apt-transport-https ca-certificates software-properties-common -y
   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
   sudo usermod -aG docker pi
   sudo curl https://download.docker.com/linux/raspbian/gpg
   sudo sh -c "echo 'deb https://download.docker.com/linux/raspbian/ stretch stable' > /etc/apt/sources.list.d/docker.list"
   sudo apt-get update && sudo apt-get upgrade
   systemctl start docker.service
   docker info

The last command should spit out a bunch information about your docker installation.

The next step is to get a production bundle for Karmen. You can get these in the
`Releases section on our GitHub <https://github.com/fragaria/karmen/releases>`_.
Just download the latest one to your Raspberry Pi's home directory and unzip it.

.. code-block:: sh

   cd
   wget -O karmen.zip https://github.com/fragaria/karmen/releases/latest/download/release.zip
   unzip -d .karmen karmen.zip
   cd .karmen

.. TODO an alternative would be to have a `release` branch, then the update would be a
   matter of git pull and container restart. wget would get replaced by git clone --branch release

It contains the following files:

- ``docker-compose.yml`` - A bluperint for all necessary services
- ``config.local.cfg`` - Configuration file that you should edit to your needs
- ``db/schema.sql`` - Initial database schema

Firstly, you should edit all the necessary stuff in ``config.local.cfg``. You can tweak 
the settings of the network autodiscovery, but you should **absolutely change the** ``SECRET_KEY``
variable for security reasons.

The ``db/schema.sql`` file is run automatically only upon the first start. The database handling will
probably change in the future. The datafiles are created on your filesystem, not inside the containers,
so no data will be lost during downtime.

Finally, you can start all of the services by running the compose file. This will download and
run the docker images with the appropriate version of Karmen.

.. code-block:: sh
  
   BASE_HOST=random-ip-address docker-compose up -d --abort-on-container-exit

``BASE_HOST`` is an address or hostname of the machine where Karmen is running and is used to call
the Python backend from the frontend UI. You will also use it to access the Javascript frontend
from your browser. The frontend is run on standard port 80 and the API is accessible on port 8080.

You can stop everything by running 

.. code-block:: sh
  
   docker-compose stop

.. toctree::
  :maxdepth: 2