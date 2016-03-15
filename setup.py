from setuptools import setup

setup(name='aws_kube_deploy',
      version='0.1',
      description='Tools for deploying to kubernetes on AWS',
      author='Matthew Mead-Briggs',
      author_email='matthew@meadbriggs.co.uk',
      install_requires=['pykube', 'boto3'],
      license='MIT',
      packages=['.'],
      zip_safe=False)
