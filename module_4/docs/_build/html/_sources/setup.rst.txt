Overview & Setup
================

Prerequisites
-------------
* Python 3.10+
* PostgreSQL 14+ running locally (or via Docker)
* ``pip`` or a virtual-environment tool

Environment Variables
---------------------

* ``DATABASE_URL`` — PostgreSQL connection string for the main database.
  Default: ``postgresql://postgres:196301@localhost:5432/gradcafe``
* ``TEST_DATABASE_URL`` — Connection string for the test database.
  Default: ``postgresql://postgres:196301@localhost:5432/gradcafe_test``

Installation
------------

.. code-block:: bash

   cd module_4
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt

Running the Application
-----------------------

.. code-block:: bash

   # 1. Load data into the database (first time only)
   python -m src.load_data

   # 2. Start the Flask server
   python -m src.app
   # Open http://localhost:5000 in your browser

How to Run Tests
----------------

.. code-block:: bash

   cd module_4
   pytest                           # runs full suite with coverage
   pytest -m web                    # only page/rendering tests
   pytest -m "db or integration"    # database & end-to-end tests
