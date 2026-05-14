"""Build the Cython-compiled solver as a regular installable package."""
from setuptools import setup, Extension
from Cython.Build import cythonize


setup(
    name='yaque_solver',
    version='1.0.0',
    packages=['yaque_solver'],
    ext_modules=cythonize(
        [Extension('yaque_solver.solver', ['yaque_solver/solver.pyx'])],
        compiler_directives={'language_level': '3'},
    ),
    zip_safe=False,
)
