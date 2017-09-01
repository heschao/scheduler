import unittest
from abc import abstractmethod, ABCMeta

from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dbtest.testing_postgresql import Postgresql


class TestDb(unittest.TestCase, metaclass=ABCMeta):
    """
    Parent class for all that needs unittest postgresql and the modesl
    """
    postgresql = None

    @classmethod
    @abstractmethod
    def base(cls):
        """
        Child must implement this
        :return:
        """

    @classmethod
    def setUpClass(cls):
        """
        Create a temporary postgresql database to test against
        First create all tables and maybe seed some data
        :return:
        """
        postgresql = Postgresql()
        engine = create_engine(postgresql.url())
        cls.base().metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        cls.session = Session()
        cls.postgresql = postgresql

    @classmethod
    def tearDownClass(cls):
        """
        Delete the test database
        :return:
        """
        cls.postgresql.stop()


# test the parent test class
Base = declarative_base()


class MyModel(Base):
    __tablename__ = 'my_model'
    id = Column(Integer, primary_key=True)


class TestMyModel(TestDb):
    """
    Test TestDb!
    """
    @classmethod
    def base(cls):
        return Base

    def test_insert(self):
        """
        Test insert a row into MyModel
        :return:
        """
        assert self.session.query(MyModel).count() == 0
        self.session.add(MyModel(id=1))
        assert self.session.query(MyModel).count()==1
