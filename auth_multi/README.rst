Auth Multi Login and Do User Merge Request
==========================================

This module added new fields in the user model to:

    1) Allow do login with multiple gmail accounts.
    2) Write log with changes in user groups.
    3) Work with the new gmail fields.


How to use
----------

1) You need immediately installed the module change the old gmail fields to
work with the new fiels that allow do login with multiples gmail account.

1.1) There is a wizard to execute this change in user view
    .. image:: auth_multi/static/src/demo/Users-OpenERP.png
    .. image:: auth_multi/static/src/demo/Users-OpenERP-action.png

2) Then you can do pre merge proposal from preference user view
.. image:: auth_multi/static/src/demo/pre_merge1.png
.. image:: auth_multi/static/src/demo/pre_merge2.png
.. image:: auth_multi/static/src/demo/pre_merge3.png

3) If the users found have the same mail that the main user the merge it
will be automatically

4) The mail with the merge request has a direct link to apply merge in the
system, must be necessary that all user involved allow the merge

