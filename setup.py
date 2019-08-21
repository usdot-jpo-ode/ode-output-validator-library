from setuptools import setup, find_packages

setup(
    name="odevalidator",
    version="0.0.5",
    description="ODE Data Validation Library",
    packages=find_packages(),
    package_data={'odevalidator': ['configs/config.ini']},
    include_package_data=True,
    test_suite="tests",
)
