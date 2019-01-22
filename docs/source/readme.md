[![Build Status](https://travis-ci.org/nvenayak/impact.svg?branch=master)](https://travis-ci.org/nvenayak/impact)
[![codecov](https://codecov.io/gh/nvenayak/impact/branch/master/graph/badge.svg)](https://codecov.io/gh/nvenayak/impact)
[![Documentation Status](https://readthedocs.org/projects/impact/badge/?version=latest)](http://impact.readthedocs.io/en/latest/?badge=latest)

# Impact: a framework for analyzing microbial physiology

Impact assists scientists and engineers to interpret data describing microbial physiology.
Impact parses raw data from common equipment such as chromatography (HPLC), 
and plate readers. Data is automatically interpreted and built into hierarchical objects
which describe the experiments and extract features.

## Install
Download a [Python 3 installation](https://www.python.org/downloads/) for your platform, 
or you can use [Anaconda](https://www.continuum.io/downloads). If you are on windows, you will need a way to install
numpy, scipy, matplotlib - packaged with Anaconda.

### Fresh install
First, clone the repository. You will need your github username and password but if you are here presumably you are logged in.
    
    git clone http://github.com/nvenayak/impact
    cd impact

Install the dependencies for the project using requirements.txt:
	
	pip install -r requirements.txt

You may also want to install the additional packages as needed, especially the plotting requirements
    
    pip install -r requirements_plotting.txt
    pip install -r requirements_modeling.txt
    pip install -r requirements_docs.txt

Install the package

    python setup.py install

Optionally, developers may wish to use the develop flag to install the package from the current location, rather than installing in the default Python installation

	python setup.py develop

### Updating
To update to the latest version, run the following in the root folder:
    
    git pull
    
### Tests
Impact comes with scripts that test the proper functioning of the package. These are available in the tests folder. Every build of impact is tested with these scripts before deployment on github.

## Documentation

The documentation is available in `docs` or a rendered version is available [here](http://impact.readthedocs.io/en/latest/)

## Starter Files
A starter ipynb which can be opened with Jupyter notebook has been provided in the Examples_and_Helpers folders. The file comes with comments which will assist users in analyzing their data. A helper file to create trial identifiers has also been provided in the Examples_and_Helpers folder.