import tempfile

import pytest


@pytest.fixture(scope="session")
def workdir():

    wdir = tempfile.TemporaryDirectory()
    yield wdir

    wdir.cleanup()
