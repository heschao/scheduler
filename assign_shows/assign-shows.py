import click
from pulp import *

from assign_shows.solver import solve_fixed_days, Config, load_yaml, get_fixed_day_configs

DEFAULT_PREF_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'show-preferences.yml')


@click.command()
@click.option('--pref-file', '-p', default=DEFAULT_PREF_FILE)
@click.option('--test-config', '-t', is_flag=True)
def main(pref_file, test_config):
    conf = Config(d=load_yaml(pref_file))
    if test_config:
        conf.test()
        return

    solutions = solve_fixed_days(fixed_day_confs=get_fixed_day_configs(conf))
    print('solution')
    print(next(solutions).assignments())


if __name__ == "__main__":
    main()
