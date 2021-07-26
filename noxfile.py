import os
import sys

import nox
from nox import Session


@nox.session
def flake(session: Session):
    session.install('flake8')
    session.run('flake8', 'src')
    session.run('flake8', 'tests')


@nox.session
def test(session: Session):
    # Adds src to the pythonpath
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + os.sep + 'src')

    session.install('pytest')
    session.run('pytest', 'tests', env={'PYTHONPATH': os.pathsep.join(sys.path)})
