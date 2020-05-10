import tempfile
import os
import io
from unittest import TestCase, mock
from swifitool import faults_inject


class TestNOP(TestCase):

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
    def test_nop_01(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "NOP", "3"])
        self.assertEqual('Architecture required when using NOP\n', err.getvalue())

    def test_nop_02(self):
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "NOP",  "3"])
        self.assertEqual(b'\x01\x02\x03\x90\x05\x06\x07\x08', self.file_out.read())

    def test_nop_03(self):
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "NOP",  "3"])
        self.assertEqual(b'\x01\x02\x03\x00\xbf\x06\x07\x08', self.file_out.read())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_nop_04(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "abc", "NOP",  "3"])
        self.assertTrue("(choose from 'x86', 'arm')" in err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_nop_05(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "NOP", "-1"])
        self.assertEqual('Address outside file content : byte -0x1\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_nop_06(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "NOP", "7"])
        self.assertEqual('Address outside file content : byte 0x8\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_nop_07(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "NOP", "abc"])
        self.assertEqual('Wrong address format : abc\n', err.getvalue())

    def test_nop_08(self):
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "NOP",  "1-3"])
        self.assertEqual(b'\x01\x90\x90\x90\x05\x06\x07\x08', self.file_out.read())

    def test_nop_09(self):
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "NOP",  "1-4"])
        self.assertEqual(b'\x01\x00\xbf\x00\xbf\x06\x07\x08', self.file_out.read())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_nop_10(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "NOP", "1-3"])
        self.assertEqual('Range of addresses for NOP must be multiple of two on ARM\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_nop_11(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "NOP", "10-3"])
        self.assertEqual('Address range empty : 10-3\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_nop_12(self, err):
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "NOP", "10-s"])
        self.assertEqual('Wrong address format : 10-s\n', err.getvalue())
