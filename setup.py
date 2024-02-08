from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys


class CustomInstall(install):
    def run(self):
        try:
            # Install the wheel file first
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "./flir/spinnaker_python-4.0.0.116-cp310-cp310-win_amd64.whl",
                ]
            )
        except subprocess.CalledProcessError as e:
            # Handle errors in the installation process
            print(f"Failed to install the wheel file: {e}")
            sys.exit(1)
        # Call the standard 'install' command
        install.run(self)


setup(
    name="nvuelab",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # List other dependencies of your package
    ],
    cmdclass={
        "install": CustomInstall,
    },
    # Include other metadata as necessary
)
