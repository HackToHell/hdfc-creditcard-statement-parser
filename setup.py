from setuptools import setup

setup(
   name='hdfcparser',
   version='1.0',
   description='HDFC Credit Card Statement converter to csv',
   author='santosh',
   author_email='santosh.siddarth123@gmail.com',
   packages=['hdfcparser'],  #same as name
   install_requires=['tabula-py'], #external packages as dependencies
)