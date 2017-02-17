from setuptools import setup

setup(
    name='es_backup',
    version='0.1',
    description='Dockerized backup scripts for elasticsearch',
    author='Johannes Gontrum',
    author_email='gontrum@me.com',
    include_package_data=True,
    license='MIT license',
    entry_points={
          'console_scripts': [
              'backup = es_backup.backup:run',
              'restore = es_backup.restore:run'
          ]
      }
)
