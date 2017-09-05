import click
from pulp import *

from sorsched.input_config import ConfigImp
from sorsched.solver2 import solve

DEFAULT_PREF_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'show-preferences.yml')


@click.command()
@click.option('--pref-file', '-p', default=DEFAULT_PREF_FILE)
@click.option('--test-config', '-t', is_flag=True)
def main(pref_file, test_config):
    conf = ConfigImp.load_from_db()
    if test_config:
        conf.test()
        return

    best_slot_assignments, best_solution = solve(conf)

    print('best slot assignments:')
    print(best_slot_assignments)
    print('best show assignemnts:')
    print(best_solution)


if __name__ == "__main__":
    main()
