.. Impact documentation master file, created by
   sphinx-quickstart on Wed Apr 25 15:07:30 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Impact's documentation!
==================================

The impact framework helps scientists and engineers analyze data for characterizing microbial physiology.
Data can be imported from analytical equipment such as HPLC and plate reader using native data
formats. From here, data is parsed into a hierarchical data structure based on the logical organization
of trials in an experiment and its identifying metadata. Then, this data can be used to generate
visualizations using a plotting package, there are many options but we rely on plotly because
it is mostly open-source, is written in js, provides interactivity within a browser, and provides
numerous interfaces to other languages such as matlab and python.

This documentation describes the use of the core impact module, which does most of the heavy-lifting.
Use of the module is demonstrated using the jupyter notebook, which is a web-based user interface
allowing scientists to store prose describing experiments and code used to analyze data and generate visualizations
together, greatly increasing the transparency of data analysis.

For first time users, visit :doc:`readme` to install the package.
Then, head over to the :doc:`quickstart` tutorial to begin importing and
analyzing data.

To learn more about the features which are automatically extracted from the
data and visualization of these features, follow the :doc:`features_0` tutorial.

Finally, all of the classes and methods which compose the module are documented
:doc:`impact`, and can be used as a guide to extend the framework to include more
raw data formats and features.

Commits including appropriate tests which extend functionality are welcomed.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   readme
   quickstart
   features_0
   features_1
   create_new_feature
   create_parser
   impact

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
