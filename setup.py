import re
from distutils.core import setup

import io

__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',  # It excludes inline comment too
    io.open('assign_shows/__init__.py', encoding='utf_8_sig').read()
).group(1)

setup(
    name='scheduler',
    version=__version__,
    include_package_data=True,
    packages=['assign_shows',],
    license='Assign kids to shows',
    long_description=open('README.md').read(), requires=['PyYAML', 'pulp', 'flask']
)