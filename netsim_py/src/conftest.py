# ----------------------------------
# Fixture for testing
#----------------------------------

import pytest
import runner.config
import tempfile


@pytest.fixture(scope='session', autouse=True)
def setup_configuration():
    runner.config.configure('unit_test')


@pytest.fixture(scope='session')
def tmp_dir():
    return tempfile.mkdtemp(prefix="netsim2_temp_test_folder_")

