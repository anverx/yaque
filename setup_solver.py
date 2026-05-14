"""Build the Cython solver in-place for local testing.

Usage:
    python setup_solver.py build_ext --inplace
"""
from setuptools import setup
from Cython.Build import cythonize

setup(
    name='yaque-solver',
    ext_modules=cythonize(
        'src/solver.pyx',
        compiler_directives={'language_level': '3'},
    ),
    zip_safe=False,
)
