from setuptools import setup, find_packages

setup(
    name="odevalidator",
    version="0.0.4",
    description="ODE Data Validation Library",
    packages=find_packages(),
    package_data={'odevalidator': ['config.ini']},
    include_package_data=True,
    test_suite="tests",
)
