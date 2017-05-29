.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3


.. contents::


Uber Oauth
==================

This module adds the following features related with Uber API


- You can do login using your Driver Uber Account, to extract info from Uber
  related with your account(Trip, Profile, Payments).

- You can manage your drivers in a new view generated to manage the trips made
  by a driver.


To manage the drivers a new menu was created.

.. image:: https://drive.google.com/uc?export=view&id=0B2kzKLGF6ZvLQXlxYTVxU3pKaFk

Inside this new menu you will see a dashboard with your drivers and submenus to
check the drivers and their trips.

.. image:: https://drive.google.com/uc?export=view&id=0B2kzKLGF6ZvLT1dlel9RRVVvcWM

In the trips view you will have a lot of tools to filter the trips to help to
manage the info extracted.

In partner view you will have two new buttons. The first one is for extract the
information from Uber using the token of the user related to the partner, this
button is located in the new page created in partner view to show uber
information. The
second one is used to redirect you to the Trips related with the current
parnter.

.. image:: https://drive.google.com/uc?export=view&id=0B2kzKLGF6ZvLZmR1ZlRZU1BVYm8

.. image:: https://drive.google.com/uc?export=view&id=0B2kzKLGF6ZvLZ2NuT2tBdVdyVms


- For the new menu you will need to have the following group.

.. image:: https://drive.google.com/uc?export=view&id=0B2kzKLGF6ZvLV0hVVXdtQjdmdlk


Installation
============

To install this module, you need to:


  - Download this module from `Vauxoo/odoo-users
    <https://github.com/Vauxoo/odoo-users>`_
  - Add the repository folder into your odoo addons-path.
  - Go to ``Settings > Module list`` search for the current name and click in
    ``Install`` button.

Configuration
=============

To Use these features you will need to configure the following things:

- You need to allow external users to signup in General Settings and set a
   template user. The new users will be a copy of this template user set.

.. image:: https://drive.google.com/uc?export=view&id=0B2kzKLGF6ZvLSktiOVhrZlZNTlk


- You need to configure the uber provider in ``Settings > Users > OAuth Providers`` and set it like allowed. 
  The information needed to complete the configuration is given by Uber API (Client Id, Client Secret).

.. image:: https://drive.google.com/uc?export=view&id=0B2kzKLGF6ZvLdmZhdjRyb19WUjQ

- A new system parameter was added. This will contain the redirect uri set in
  Uber API, This value MUST be the same to the redirect uri set in Uber API.

.. image:: https://drive.google.com/uc?export=view&id=0B2kzKLGF6ZvLaExuR2M2MXFvclE


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/Vauxoo/odoo-users/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Contributors
------------

* Jose Morales <jose@vauxoo.com>

Maintainer
----------

.. image:: https://www.vauxoo.com/logo.png
    :alt: Vauxoo
    :target: https://vauxoo.com

This module is maintained by Vauxoo.

a latinamerican company that provides training, coaching,
development and implementation of enterprise management
sytems and bases its entire operation strategy in the use
of Open Source Software and its main product is odoo.

To contribute to this module, please visit http://www.vauxoo.com.

