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
    package_data={'sorsched':['templates/*','static/*']},
    packages=['sorsched','dbtest'],
    scripts=['bin/init-db'],
    description='Assign kids to shows',
    author='Chao Chen',
    author_email='chao@cranient.com',
    url='https://github.com/heschao/scheduler',
    long_description=open('README.md').read(), requires=['PyYAML', 'pulp', 'flask', 'sqlalchemy', 'numpy', 'wtforms']
)