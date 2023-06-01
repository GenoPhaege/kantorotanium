# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['kantorotanium']

package_data = \
{'': ['*'], 'kantorotanium': ['data_files/*']}

install_requires = \
['dataclasses-json>=0.5.7,<0.6.0',
 'logzero>=1.7.0,<2.0.0',
 'more-itertools>=8.6.0,<9.0.0',
 'ortools>=9.6.2534,<10.0.0',
 'requests>=2.31.0,<3.0.0']

entry_points = \
{'console_scripts': ['kantorotanium = kantorotanium.__main__:main']}

setup_kwargs = {
    'name': 'kantorotanium',
    'version': '0.0.1',
    'description': 'Eve Online: optimize compressed ore purchases',
    'long_description': 'None',
    'author': 'Chris Danis',
    'author_email': 'cdanis@gmail.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<3.12',
}


setup(**setup_kwargs)

