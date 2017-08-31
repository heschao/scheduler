import click
from pulp import *

from sorsched.solver import solve_fixed_days, load_yaml, get_fixed_day_configs
from sorsched.input_config import Config

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
    optimal_solution = next(solutions)
    print('show days:')
    print(optimal_solution.config)
    print('assignments: ')
    print(optimal_solution.assignments())


if __name__ == "__main__":
    main()
