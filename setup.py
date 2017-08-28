from distutils.core import setup

setup(
    name='scheduler',
    version='0.1dev',
    packages=['assign_shows',],
    license='Assign kids to shows',
    long_description=open('README.md').read(), requires=['PyYAML', 'pulp', 'flask']
)