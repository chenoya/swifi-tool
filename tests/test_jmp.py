import tempfile
import os
import io
from unittest import TestCase, mock
from swifitool import faults_inject


# The binary is generated using nasm and decompiled using objdump
#
# For example:
# > cat jmp.asm
# [BITS 32]
# a: xor eax, eax
# b: xor ebx, ebx
# c: xor ecx, ecx
# jmp b
# d: xor edx, edx
#
# > nasm -f bin jmp.asm
#
# > xxd -p jmp
# 31c031db31c9ebfa31d2
#
# > objdump -D -Mintel,x86-64 -b binary -m i386 jmp
# jmp:     file format binary
# Disassembly of section .data:
# 00000000 <.data>:
#    0:	31 c0                	xor    eax,eax
#    2:	31 db                	xor    ebx,ebx
#    4:	31 c9                	xor    ecx,ecx
#    6:	eb fa                	jmp    0x2
#    8:	31 d2                	xor    edx,edx


class TestJMP(TestCase):

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

    def test_jmp_01(self):
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\xeb\xfa\x31\xd2')
        self.file_in.flush()
        #    0:	31 c0                	xor    eax,eax
        #    2:	31 db                	xor    ebx,ebx
        #    4:	31 c9                	xor    ecx,ecx
        #    6:	eb fa                	jmp    0x2
        #    8:	31 d2                	xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP",  "0x6",  "0x8"])
        self.assertEqual(b'\x31\xc0\x31\xdb\x31\xc9\xeb\x00\x31\xd2', self.file_out.read())
        #    0:	31 c0                	xor    eax,eax
        #    2:	31 db                	xor    ebx,ebx
        #    4:	31 c9                	xor    ecx,ecx
        #    6:	eb 00                	jmp    0x8
        #    8:	31 d2                	xor    edx,edx

    def test_jmp_02(self):
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\x66\xe9\xf8\xff\x31\xd2')
        self.file_in.flush()
        #    0:	31 c0                	xor    eax,eax
        #    2:	31 db                	xor    ebx,ebx
        #    4:	31 c9                	xor    ecx,ecx
        #    6:	66 e9 f8 ff          	jmp    0x2     ; using size 'word' when compiling
        #    a:	31 d2                	xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP",  "0x6",  "0x0"])
        self.assertEqual(b'\x31\xc0\x31\xdb\x31\xc9\x66\xe9\xf6\xff\x31\xd2', self.file_out.read())
        #    0:  31 c0                  xor    eax,eax
        #    2:  31 db                  xor    ebx,ebx
        #    4:  31 c9                  xor    ecx,ecx
        #    6:  66 e9 f6 ff            jmp    0x0
        #    a:  31 d2                  xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP", "0x7", "0x0"])
        self.file_out.seek(0)
        self.assertEqual(b'\x31\xc0\x31\xdb\x31\xc9\x66\xe9\xf6\xff\x31\xd2', self.file_out.read())
        # can also omit counting the 0x66

    def test_jmp_04(self):
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\xe9\xf7\xff\xff\xff\x31\xd2')
        self.file_in.flush()
        #    0:	31 c0                	xor    eax,eax
        #    2:	31 db                	xor    ebx,ebx
        #    4:	31 c9                	xor    ecx,ecx
        #    6:	e9 f7 ff ff ff       	jmp    0x2     ; using size 'dword' when compiling
        #    b:	31 d2                	xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP",  "0x6",  "0x0"])
        self.assertEqual(b'\x31\xc0\x31\xdb\x31\xc9\xe9\xf5\xff\xff\xff\x31\xd2', self.file_out.read())
        #    0:  31 c0                  xor    eax,eax
        #    2:  31 db                  xor    ebx,ebx
        #    4:  31 c9                  xor    ecx,ecx
        #    6:  e9 f5 ff ff ff         jmp    0x0
        #    b:  31 d2                  xor    edx,edx

    def test_jmp_05(self):
        self.file_in.write(b'\xe9\x00\x00\x00\x00\x31\xd2')
        self.file_in.flush()
        #    0:	e9 00 00 00 00       	jmp    0x5
        #    5:	31 d2                	xor    edx,edx
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP",  "0x0",  "0x0"])
        self.assertEqual(b'\xe9\xfb\xff\xff\xff\x31\xd2', self.file_out.read())
        #    0:  e9 fb ff ff ff         jmp    0x0
        #    5:  31 d2                  xor    edx,edx

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jmp_06(self, err):
        self.file_in.write(b'\x00\x01\x02\x03\x04\x05\x06\x07')
        self.file_in.flush()
        with self.assertRaises(Exception):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP", "0x1000", "0x0"])
        # TODO should print a user friendly message in this case

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jmp_07(self, err):
        self.file_in.write(b'\x00\x01\x02\x03\x04\x05\x06\x07')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP", "abc", "0x0"])
        self.assertEqual('Wrong address format : abc\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jmp_08(self, err):
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\xeb\xfa\x31\xd2')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP", "0x6", "0x1000"])
        self.assertEqual('Warning: Target outside the file\nTarget value out of range : 4088\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jmp_09(self, err):
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\xeb\xfa\x31\xd2')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP", "0x6", "abc"])
        self.assertEqual('Invalid target for JMP : abc\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jmp_10(self, err):
        self.file_in.write(b'\x31\xc0\x31\xdb\x31\xc9\xeb\xfa\x31\xd2')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP", "0x0", "0x0"])
        self.assertEqual('Unknow opcode at JMP address : 0x31\n', err.getvalue())

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jmp_11(self, err):
        self.file_in.write(b'\x66\xc0\x31\xdb\x31\xc9\xeb\xfa\x31\xd2')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "x86", "JMP", "0x0", "0x0"])
        self.assertEqual('Unknow opcode at JMP address : 0xc0\n', err.getvalue())

    def test_jmp_12(self):
        self.file_in.write(b'\x07\x00\x00\xea')
        self.file_in.flush()
        #    0:	ea 00 00 07             b      0x24
        faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "JMP",  "0x0",  "0x2"])
        self.assertEqual(b'\xfe\xff\xff\xea', self.file_out.read())
        #    0:	ea ff ff fe             b      0x0

    @mock.patch('sys.stderr', new_callable=io.StringIO)
    def test_jmp_13(self, err):
        self.file_in.write(b'\x00\x01\x02\x03\x04\x05\x06\x07')
        self.file_in.flush()
        with self.assertRaises(SystemExit):
            faults_inject.main(["-i", self.file_in.name, "-o", self.file_out.name, "-a", "arm", "JMP", "0x0", "0x0"])
        self.assertEqual('Unknow opcode at JMP address : 0x3\n', err.getvalue())
