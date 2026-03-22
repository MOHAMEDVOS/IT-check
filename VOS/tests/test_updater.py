import os
import subprocess
from unittest.mock import patch, MagicMock

# Assuming updater is in modules/
from modules import updater

def test_updater_strips_meipass_variables():
    """
    Test that when apply_update runs, it strips _MEIPASS and _MEIPASS2
    from the environment before spawning the wscript subprocess.
    """
    # Simulate being a frozen PyInstaller app
    with patch("sys.frozen", True, create=True), \
         patch("sys.executable", "C:\\fake\\app\\VOS.exe"), \
         patch("requests.get") as mock_get, \
         patch("subprocess.Popen") as mock_popen, \
         patch("os._exit") as mock_exit, \
         patch("builtins.open"), \
         patch.dict(os.environ, {"_MEIPASS2": "C:\\fake\\temp\\_MEI12345", "_MEIPASS": "C:\\fake\\temp\\_MEI12345"}):
         
        # Mock requests.get to return a dummy response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"dummyexecontent"]
        mock_get.return_value = mock_response

        # Call apply_update
        updater.apply_update("http://fake.url/vos.exe")

        # Verify Popen was called
        assert mock_popen.called, "subprocess.Popen was not called to launch the VBS script."
        
        # Check the kwargs passed to Popen
        _, kwargs = mock_popen.call_args
        
        # The environment passed to Popen should NOT contain _MEIPASS2
        assert 'env' in kwargs, "updater did not pass an explicit 'env' to subprocess.Popen"
        assert "_MEIPASS2" not in kwargs['env'], "_MEIPASS2 was leaked into the subprocess environment!"
        assert "_MEIPASS" not in kwargs['env'], "_MEIPASS was leaked into the subprocess environment!"
