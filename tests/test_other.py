import tempfile
import os
from unittest import TestCase
from swifitool import faults_inject


class TestOther(TestCase):

    file_in = None
    file_out = None
    file_cmd = None

    def setUp(self):
        super().setUp()
        self.file_in = tempfile.NamedTemporaryFile(delete=False)
        self.file_out = tempfile.NamedTemporaryFile(delete=False)
        self.file_cmd = tempfile.NamedTemporaryFile(delete=False)

    def tearDown(self):
        self.file_in.close()
        os.unlink(self.file_in.name)
        self.file_out.close()
        os.unlink(self.file_out.name)
        self.file_cmd.close()
        os.unlink(self.file_cmd.name)

    def test_other_01(self):
        """Reading two faults from a file."""
        self.file_in.write(b'\x01\x02\x03\x04\x05\x06\x07\x08')
        self.file_in.flush()
        self.file_cmd.write(b'NOP 0x3\nNOP 0x5')
        self.file_cmd.flush()
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "-f", self.file_cmd.name])
        self.assertEqual(b'\x01\x02\x03\x90\x05\x90\x07\x08', self.file_out.read())

    # Not performed since it requires user interaction.
    # def test_other_02(self):
    #     """Showing the GUI."""
    #     self.file_in.write(b'\x01\x02\x03\x04\x05\x06\x07\x08' * 10)
    #     self.file_in.flush()
    #     self.file_cmd.write(b'NOP 0x3\nNOP 0x5')
    #     self.file_cmd.flush()
    #     faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "-g", "NOP", "0x3"])
    #     self.assertEqual(b'\x01\x02\x03\x90\x05\x06\x07\x08' + b'\x01\x02\x03\x04\x05\x06\x07\x08' * 9, self.file_out.read())
