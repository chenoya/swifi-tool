import tempfile
import os
import io
from unittest import TestCase, mock
from swifitool import faults_inject


class TestZ1B(TestCase):

    file_in = None
    file_out = None

    def setUp(self):
        super().setUp()
        self.file_in = tempfile.NamedTemporaryFile(delete=False)
        self.file_in.write(b'\x01\x02\x03\x04\x05\x06\x07\x08')
        self.file_in.flush()
        self.file_out = tempfile.NamedTemporaryFile(delete=False)

    def tearDown(self):
        self.file_in.close()
        os.unlink(self.file_in.name)
        self.file_out.close()
        os.unlink(self.file_out.name)

    def test_z1b_01(self):
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "Z1B",  "3"])
        self.assertEqual(b'\x01\x02\x03\x00\x05\x06\x07\x08', self.file_out.read())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1b_02(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "Z1B", "-1"])
        self.assertEqual('Address outside file content : byte -0x1\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1b_03(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "Z1B", "1000"])
        self.assertEqual('Address outside file content : byte 0x3e8\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1b_04(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "Z1B", "abc"])
        self.assertEqual('Wrong address format : abc\n', err.getvalue())
