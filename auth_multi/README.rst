Oauth Multi Users
==========================================

This module allows you relate multiple accounts to the same user using oauth protocol.

How it works
------------

- When this module is installed the fields used to do login using oauth are
  replaced to the new one created by this module. This new field is a one2many
  relation to allow add as many accounts as posible to a user.

    .. image:: https://drive.google.com/uc?export=view&id=1Nv4a37Wyw94X2ZFBzWeRqTV4JAOMYaVr

How to use
----------

The preferece view was changed to show the accounts related and a new button to show a wizard to begin the claim process

    .. image:: https://drive.google.com/uc?export=view&id=1vdE80AYwGJicmw-r2Wffx8YUEJ3PdEB8

- The new wizard shows three fields to help you to search and start the claim process.

- The first one shows the main user in the claim. The oauth information of the users found will be added to this user. This field will filled automatically with the user which started the process

- The second one shows the field which you want to search the users with(Name, Email).

- The last one is an empty field which you must fill out to search the users you want to claim

Whether an user is found(or not) using the values you filled out, a message will be showed indicating the next action

.. image:: https://drive.google.com/uc?export=view&id=1Jj2fS5O4oCyJWe47axqVY_8-WzAQnP-D
.. image:: https://drive.google.com/uc?export=view&id=1uSenVZ3l4XBP4IEIsPNF0GfK1jMSckzo

Whether everything is ok, the users involved in the claim receive an email with a link to complete the process if they agree with it.

This window shows the users involved and if they already authorized the process. You have to apply if you agree

.. image:: https://drive.google.com/uc?export=view&id=1D0oJeaEbdsmviVYh6-5E9XUyXZnySSd6
.. image:: https://drive.google.com/uc?export=view&id=18xkPCdxQzvBgVoTJyR2nFdBiGZczUocW

When you apply the merge request you have to wait for the other users involved. The process will be completed when all of them apply the merge.

.. image:: https://drive.google.com/uc?export=view&id=1Z3EPIwW2JzkbXE9GZ2wNnAf4wmJmg6I-

When the last one complete the process, the merge will be applied. The relations to the users will be updated to the main user(Which started the claim) allowing the removal or inactivation of them

.. image:: https://drive.google.com/uc?export=view&id=1udEUf7M2u_w-AIPDVJZvkZFsLcUfhsvd
