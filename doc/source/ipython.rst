=================
IPython Tutorials
=================

These IPython (http://ipython.org) notebooks show the usage of the PyEMMA API in
action and also describe the workflow of Markov model building.

You can obtain a copy of all notebooks and most of the used data
`here <https://github.com/markovmodel/PyEMMA_IPython/archive/devel.zip>`_.
Note that the trajectory of the D.E. Shaw BPTI simulation trajectory is not included
in this archive, since we're not permitted to share this data. Thus the corresponding
notebooks can't be run without obtaining the simulation trajectory independently.

Application walkthroughs
========================

.. toctree::
   :maxdepth: 1

   generated/pentapeptide_msm

   generated/MSM_BPTI

   generated/trypsin_benzamidine_hmm


By means of application examples, these notebooks give an overview of following methods:

   * Featurization and MD trajectory input
   * Time-lagged independent component analysis (TICA)
   * Clustering
   * Markov state model (MSM) estimation and validation
   * Computing Metastable states and structures, coarse-grained MSMs
   * Hidden Markov Models (HMM)
   * Transition Path Theory (TPT)


Methods
=======

In this section we will give you in-depth tutorials on specific methods or concepts.

.. toctree::
   :maxdepth: 1

   generated/feature_selection

   generated/model_selection_validation

   generated/tpt


