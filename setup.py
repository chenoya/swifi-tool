import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='swifitool',
    version='1.0.0',
    author='Chenoy Antoine',
    description='Inject faults into binary files based on several fault models.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/chenoya/swifi-tool',
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=['tkinter']
)
