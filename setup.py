from setuptools import setup, find_packages

setup(
    name="odevalidator",
    version="0.0.2",
    author_email="fake@email.com",
    description="ODE Data Validation Library",
    packages=['odevalidator'],
    package_data={'': ['config.ini']},
    include_package_data=True,
)
