import nox
from nox import Session


@nox.session
def test(session: Session):
    session.install('pytest')
    session.run('pytest', 'tests')
