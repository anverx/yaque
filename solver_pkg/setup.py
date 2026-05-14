"""Build the Cython-compiled solver as a regular installable package."""
from setuptools import setup, Extension
from Cython.Build import cythonize


solver_ext = Extension(
    'yaque_solver.solver',
    ['yaque_solver/solver.pyx'],
    extra_compile_args=['-O3', '-ffast-math'],
)


setup(
    name='yaque_solver',
    version='1.0.0',
    packages=['yaque_solver'],
    ext_modules=cythonize(
        [solver_ext],
        compiler_directives={'language_level': '3'},
    ),
    zip_safe=False,
)
