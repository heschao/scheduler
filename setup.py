import re
from distutils.core import setup

import io

__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',  # It excludes inline comment too
    io.open('sorsched/__init__.py', encoding='utf_8_sig').read()
).group(1)

setup(
    name='sorsched',
    version=__version__,
    include_package_data=True,
    packages=['sorsched',],
    description='Assign kids to shows',
    author='Chao Chen',
    author_email='chao@cranient.com',
    long_description=open('README.md').read(), requires=['PyYAML', 'pulp', 'flask']
)