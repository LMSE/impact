from setuptools import setup

setup(
    name='impact',
    version='0.5.0',
    packages=['impact'],
    url='www.github.com/nvenayak/impact',
    license='',
    author='Naveen Venayak',
    author_email='naveen.venayak@gmail.com',
    description='Data analysis toolbox for microbial fermentation kinetics.',
    install_requires=['cobra>=0.4.1',
                      'dill>=0.2.4',
                      'Django>=1.9.5',
                      'lmfit==0.8.3',
                      'matplotlib>=1.5.1',
                      'numpy>=1.10.4',
                      'plotly>=1.9.10',
                      'pyexcel-xlsx>=0.1.0',
                      'scipy>=0.17.0',
                      'colorlover',
                      'django-bootstrap-form',
                      'django-bootstrap3',
                      'sphinx_bootstrap_theme',
                      'nbsphinx',
                      'numpydoc',
                      'pandas']
)