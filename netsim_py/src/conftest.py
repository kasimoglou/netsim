# ----------------------------------
# Fixture for testing
#----------------------------------

import pytest
import runner.config
import tempfile


@pytest.fixture(scope='session', autouse=True)
def setup_configuration():
    '''\
    Ensure that the configuration file is read and the 
    'unit_test' section is used.
    '''
    runner.config.configure('unit_test')

@pytest.fixture(scope='session')
def tmp_dir(request):
    '''\
    Create a temporary test folder.
    '''
    dirname = tempfile.mkdtemp(prefix="netsim2_temp_test_folder_")
    def fin():
        import shutil
        shutil.rmtree(dirname, ignore_errors=True)
    request.addfinalizer(fin)
    return dirname


