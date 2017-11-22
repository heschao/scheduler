from typing import List

import pandas as pd
import click
import logging
from dbtest.testdb import TestDb
from sorsched import db, models
from sorsched.data import Instrument
from sorsched.models import Show, Slot, Student, ShowPreference, ShowInstrument, StudentInstrument, SlotAvailable
from sorsched.views import run_optimization

# shows
grunge = Show(name='Big 4 of Grunge', min_students=5, max_students=10)
women = Show(name='Women of Rock', min_students=5, max_students=10)
iron = Show(name='Iron Maiden', min_students=5, max_students=10)
floyd = Show(name='Pink Floyd', min_students=5, max_students=10)

# slot map
slot_map = {
    'Grunge':'Tue',
    'Women' : 'Thu',
    'Iron' : 'Fri',
    'Floyd' : 'Sat'
}
show_map = {'Grunge': grunge,
            'Women': women,
            'Iron': iron,
            'Floyd': floyd
            }


def populate_db(session):
    # instruments
    instruments =[]
    for instrument in Instrument:
        instruments.append(models.Instrument(name=instrument.value))

    shows = [grunge,women,iron,floyd]

    insmap = {
        'g':{
            'g':(2,5),
            'd':(2,5),
            'b':(0,5),
            'v':(0,5),
            'k':(0,5),
        },
        'w':{
            'g':(2,5),
            'd':(2,5),
            'b':(0,5),
            'v':(0,5),
            'k':(0,5),
        },
        'i':{
            'g':(2,5),
            'd':(2,5),
            'b':(0,5),
            'v':(0,5),
            'k':(0,5),
        },
        'f':{
            'g':(2,5),
            'd':(2,5),
            'b':(0,5),
            'v':(0,5),
            'k':(0,5),
        }
    }

    show_instruments = []
    for show_abbrev,show in (('g',grunge),('w',women),('i',iron),('f',floyd)):
        for ins_abbrev,ins in (('g',Instrument.Guitar),('d',Instrument.Drums),('b',Instrument.Bass),('k',Instrument.Keys),('v',Instrument.Vocals)):
            mn,mx = insmap[show_abbrev][ins_abbrev]
            show_instruments.append(
                ShowInstrument(show_name=show.name,instrument_name=ins.value,min_instruments=mn,max_instruments=mx),
            )

    tue = Slot(name='Tue', max_shows=1)
    thu = Slot(name='Thu', max_shows=1)
    fri = Slot(name='Fri', max_shows=1)
    sat = Slot(name='Sat', max_shows=1)
    slots = [tue,thu,fri,sat]

    session.add_all(instruments + shows + slots + show_instruments)


def parse_slot_availabilities(student_name,row)->List[SlotAvailable]:
    x=[]
    for col,slot_name in slot_map.items():
        if row[col]<5:
            x.append(SlotAvailable(student_name=student_name,slot_name=slot_name))
    return x


def parse_show_preferences(student_name,row)->List[ShowPreference]:
    show_preferences=[]
    raw_preference={}
    n_shows = len(show_map)
    for col, show in show_map.items():
        p = n_shows + 1 -row[col]
        raw_preference[col]=p

    for col, show in show_map.items():
        show_preferences.append(ShowPreference(student_name=student_name, show_name=show.name, preference=raw_preference[col]))
    return show_preferences


def load_preferences(session, file):
    x=pd.read_csv(file,index_col='Name')
    students = [Student(name=name) for name in x.index]

    instrument_map = {
        'G':Instrument.Guitar,
        'B':Instrument.Bass,
        'V':Instrument.Vocals,
        'D':Instrument.Drums,
        'K':Instrument.Keys,
    }

    show_preferences = []
    student_instruments=[]
    slot_availabilities=[]
    for student_name,row in x.iterrows():
        # show preferences
        show_preferences+=parse_show_preferences(student_name=student_name,row=row)

        # student instrument
        instrument_name = instrument_map[row.Instrument[0]].value
        student_instruments.append(StudentInstrument(student_name=student_name,instrument_name=instrument_name))

        # slot availability
        slot_availabilities+=parse_slot_availabilities(student_name=student_name,row=row)

    session.add_all(students + show_preferences + student_instruments+ slot_availabilities)



@click.command()
@click.option('--filename',default='signups.csv')
def main(filename):
    populate_db(db.session)
    load_preferences(session=db.session,file=filename)
    run_optimization(db.session)
    db.session.commit()

if __name__ == "__main__":
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    main()