"""Local p4a recipe for the yaque_solver Cython package.

Points at our in-tree `yaque_solver/` package and builds it like any
other Cython recipe.
"""
import os
import shutil
from os.path import join, dirname, abspath, exists

from pythonforandroid.recipe import CythonRecipe


class YaqueSolverRecipe(CythonRecipe):
    name = 'yaque_solver'
    version = '1.0.0'
    depends = ['setuptools']
    # No external URL — we use local source.
    url = None

    # Path to the in-tree package (relative to this recipe file).
    @property
    def local_source(self) -> str:
        return abspath(join(dirname(__file__), '..', '..', 'solver_pkg'))

    def download_if_necessary(self):
        # No remote download; we copy from local source below.
        info = self.local_source
        if not exists(info):
            raise IOError(
                f'yaque_solver local source not found at {info}'
            )

    def prepare_build_dir(self, arch):
        # CythonRecipe expects the source to be extracted into the build dir.
        # We just copy our local package there.
        build_dir = self.get_build_dir(arch)
        if exists(build_dir):
            shutil.rmtree(build_dir)
        shutil.copytree(self.local_source, build_dir)


recipe = YaqueSolverRecipe()
