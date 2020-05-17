import tempfile
import os
import io
from unittest import TestCase, mock
from swifitool import faults_inject


# The binary is generated using nasm and decompiled using objdump
#
# For example:
# > cat jcc.asm
# [BITS 32]
# a: xor eax, eax
# b: xor ebx, ebx
# c: xor ecx, ecx
# jne b
# d: xor edx, edx
#
# > nasm -f bin jcc.asm
#
# > xxd -p jcc
# 31c031db31c975fa31d2
#
# > objdump -D -Mintel,x86-64 -b binary -m i386 jcc
# jcc:     file format binary
# Disassembly of section .data:
# 00000000 <.data>:
#    0:	31 c0                	xor    eax,eax
#    2:	31 db                	xor    ebx,ebx
#    4:	31 c9                	xor    ecx,ecx
#    6:	75 fa                	jne    0x2
#    8:	31 d2                	xor    edx,edx


class TestJCC(TestCase):

    file_in = None
    file_out = None

    def setUp(self):
        super().setUp()
        self.file_in = tempfile.NamedTemporaryFile(delete=False)
        self.file_out = tempfile.NamedTemporaryFile(delete=False)

    def tearDown(self):
        self.file_in.close()
        os.unlink(self.file_in.name)
        self.file_out.close()
        os.unlink(self.file_out.name)

    def test_jcc_01(self):
        """Simple use case test (JNE rel8)."""
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\x75\xfa\x31\xd2')
        self.file_in.flush()
        #    0:  31 c0                  xor    eax,eax
        #    2:  31 db                  xor    ebx,ebx
        #    4:  31 c9                  xor    ecx,ecx
        #    6:  75 fa                  jne    0x2
        #    8:  31 d2                  xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC",  "0x6",  "0x8"])
        self.assertEqual(b'\x31\xc0\x31\xdb\x31\xc9\x75\x00\x31\xd2', self.file_out.read())
        #    0:  31 c0                  xor    eax,eax
        #    2:  31 db                  xor    ebx,ebx
        #    4:  31 c9                  xor    ecx,ecx
        #    6:  75 00                  jne    0x8
        #    8:  31 d2                  xor    edx,edx

    def test_jcc_02(self):
        """Simple use case test (JNE rel16)."""
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\x66\x0f\x85\xf9\xff\x31\xd2')
        self.file_in.flush()
        #    0:  31 c0                  xor    eax,eax
        #    2:  31 db                  xor    ebx,ebx
        #    4:  31 c9                  xor    ecx,ecx
        #    6:  66 0f 85 f9 ff         jne    0x4
        #    b:  31 d2                  xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC",  "0x6",  "0x0"])
        self.assertEqual(b'\x31\xc0\x31\xdb\x31\xc9\x66\x0f\x85\xf5\xff\x31\xd2', self.file_out.read())
        #    0:  31 c0                  xor    eax,eax
        #    2:  31 db                  xor    ebx,ebx
        #    4:  31 c9                  xor    ecx,ecx
        #    6:  66 0f 85 f5 ff         jne    0x0
        #    b:  31 d2                  xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC", "0x7", "0x0"])
        self.file_out.seek(0)
        self.assertEqual(b'\x31\xc0\x31\xdb\x31\xc9\x66\x0f\x85\xf5\xff\x31\xd2', self.file_out.read())
        # can also omit counting the 0x66

    def test_jcc_03(self):
        """Simple use case test (JNE rel32)."""
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\x0f\x85\xf6\xff\xff\xff\x31\xd2')
        self.file_in.flush()
        #    0:  31 c0                  xor    eax,eax
        #    2:  31 db                  xor    ebx,ebx
        #    4:  31 c9                  xor    ecx,ecx
        #    6:  0f 85 f6 ff ff ff      jne    0x2
        #    c:  31 d2                  xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC",  "0x6",  "0x0"])
        self.assertEqual(b'\x31\xc0\x31\xdb\x31\xc9\x0f\x85\xf4\xff\xff\xff\x31\xd2', self.file_out.read())
        #    0:  31 c0                  xor    eax,eax
        #    2:  31 db                  xor    ebx,ebx
        #    4:  31 c9                  xor    ecx,ecx
        #    6:  0f 85 f4 ff ff ff      jne    0x0
        #    c:  31 d2                  xor    edx,edx

    def test_jcc_04(self):
        """Simple use case test (JNE rel32 first in the file)."""
        self.file_in.write(b'\x0f\x85\x00\x00\x00\x00\x31\xd2')
        self.file_in.flush()
        #    0:  0f 85 00 00 00 00      jne    0x6
        #    6:  31 d2                  xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC",  "0x0",  "0x0"])
        self.assertEqual(b'\x0f\x85\xfa\xff\xff\xff\x31\xd2', self.file_out.read())
        #    0:  0f 85 fa ff ff ff      jne    0x0
        #    6:  31 d2                  xor    edx,edx

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jcc_05(self, err):
        """Jump address outside the file."""
        self.file_in.write(b'\x00\x01\x02\x03\x04\x05\x06\x07')
        self.file_in.flush()
        with self.assertRaises(Exception):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC", "0x1000", "0x0"])
        # TODO should print a user friendly message in this case

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jcc_06(self, err):
        """Not a number jump address."""
        self.file_in.write(b'\x00\x01\x02\x03\x04\x05\x06\x07')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC", "abc", "0x0"])
        self.assertEqual('Wrong address format : abc\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jcc_07(self, err):
        """Target address outside of possible range."""
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\x75\xfa\x31\xd2')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC", "0x6", "0x1000"])
        self.assertEqual('Warning: Target outside the file\nTarget value out of range : 4088\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jcc_08(self, err):
        """Not a number target address."""
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\x75\xfa\x31\xd2')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC", "0x6", "abc"])
        self.assertEqual('Invalid target for JCC : abc\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jcc_09(self, err):
        """Not a supported jump instruction at the given address."""
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\x75\xfa\x31\xd2')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC", "0x0", "0x0"])
        self.assertEqual('Unknow opcode at JCC address : 0x31\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jcc_10(self, err):
        """Not a supported jump instruction at the given address (after 0x66)."""
        self.file_in.write(b'\x66\xc0\x31\xdb\x31\xc9\x75\xfa\x31\xd2')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JCC", "0x0", "0x0"])
        self.assertEqual('Unknow opcode at JCC address : 0xc0\n', err.getvalue())

    def test_jcc_11(self):
        """Simple use case test (ARM BNE instruction)."""
        self.file_in.write(b'\x07\x00\x00\x1a')
        self.file_in.flush()
        #    0:	1a 00 00 07             bne    0x24
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "JCC",  "0x0",  "0x2"])
        self.assertEqual(b'\xfe\xff\xff\x1a', self.file_out.read())
        #    0:	1a ff ff fe             bne    0x0

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jcc_12(self, err):
        """Not a supported jump instruction at the given address (ARM)."""
        self.file_in.write(b'\x00\x01\x02\x03\x04\x05\x06\x07')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "JCC", "0x0", "0x0"])
        self.assertEqual('Unknow opcode at JCC address : 0x3\n', err.getvalue())
