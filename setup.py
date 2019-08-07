from setuptools import setup

setup(
    name='IKEA-Tradfri-plugin',
    version='2.0.0',
    url='https://github.com/moroen/IKEA-Tradfri-plugin',
    author='moroen',
    author_email='moroen@gmail.com',
    description='Controlling IKEA-Tradfri from Domoticz',
    packages=[],
    dependency_links=['http://github.com/moroen/ikea-tradfri/tarball/master#egg=ikeatradfri-0.0.1'],
    include_package_data=True,
    setup_requires=['Cython'],
    install_requires=['ikeatradfri==0.0.1'],
    scripts=[],
)
