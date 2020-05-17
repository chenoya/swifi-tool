import tempfile
import os
import io
from unittest import TestCase, mock
from swifitool import faults_inject


class TestZ1W(TestCase):

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

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1w_01(self, err):
        """Missing word size parameter."""
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "Z1W", "3"])
        self.assertEqual('Word size required when using Z1W\n', err.getvalue())

    def test_z1w_02(self):
        """Simple use case test."""
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "2", "Z1W",  "3"])
        self.assertEqual(b'\x01\x02\x03\x00\x00\x06\x07\x08', self.file_out.read())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1w_03(self, err):
        """Negative word size."""
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "-1", "Z1W",  "3"])
        self.assertEqual('Word size must be positive\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1w_04(self, err):
        """Giant word size that would require to write outside the file."""
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "1000", "Z1W", "3"])
        self.assertEqual('Address outside file content : byte 0x8\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1w_05(self, err):
        """Negative address."""
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "2", "Z1W", "-1"])
        self.assertEqual('Address outside file content : byte -0x1\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1w_06(self, err):
        """Address outside the file."""
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "2", "Z1W", "1000"])
        self.assertEqual('Address outside file content : byte 0x3e8\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1w_07(self, err):
        """Not a number address."""
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "2", "Z1W", "abc"])
        self.assertEqual('Wrong address format : abc\n', err.getvalue())

    def test_z1w_08(self):
        """Simple use case with a range."""
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "2", "Z1W",  "1-6"])
        self.assertEqual(b'\x01\x00\x00\x00\x00\x00\x00\x08', self.file_out.read())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1w_09(self, err):
        """Range does not contains an integer number of words."""
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "2", "Z1W", "1-3"])
        self.assertEqual('Range of addresses for Z1W must be multiple of the word length\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1w_10(self, err):
        """Invalid range."""
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "2", "Z1W", "10-3"])
        self.assertEqual('Address range empty : 10-3\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_z1w_11(self, err):
        """Invalid range."""
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-w", "2", "Z1W", "10--3"])
        self.assertEqual('Wrong address format : 10--3\n', err.getvalue())
