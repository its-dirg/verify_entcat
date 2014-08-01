.. _Run:

Run
===

Open a terminal::

    cd [your path]/verify_entcat/
    python sp.py conf -D <url of discovery server>

To use a WAYF service (instead of discovery server) start the SP with::

    python sp.py conf -W <url of WAYF service>
    
Note that you should not have the .py extension on the config.py while running the program

The SP should now be up, and reachable at the URL <BASE> (where <BASE> is configured in conf.py, see
:doc:`Setup </setup>`).


Executing the tests
-------------------
When executing a test, selected by clicking the associated button "Run test", you will be redirected to choose an IdP
(from the ones configured in the metadata) and prompted to login.

All tests can be executed in a sequence, only requiring login once, by clicking the button "Run all tests".

The complete result of a test, including missing or extra attributes returned from the IdP, can be viewed by expanding
the row of the test.


Overview of test results
------------------------
A persistent overview of the latest test result for all IdPs can be found at the URL <BASE>/overview (where <BASE> is
configured in conf.py, see :doc:`Setup </setup>`). Information about the tests can be found by clicking the headline of
the corresponding column. Complete information about the IdPs result on a test can be found by hovering the mouse over
the cell.


