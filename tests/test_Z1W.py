from unittest import TestCase

import faults_inject


class Test_Z1W(TestCase):
    def test_one_zero(self):
        faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 -w 2 Z1W 0x0'.split(' '))
        fib = open('fib', 'rb')
        fib2 = open('fib2', 'rb')
        self.assertEqual(ord(fib2.read(1)), 0x0)
        self.assertEqual(ord(fib2.read(1)), 0x0)
        fib.read(2)
        self.assertEqual(fib.read(), fib2.read())
        fib.close()
        fib2.close()

    def test_two_zero(self):
        faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 -w 2 Z1W 0x0 Z1W 0x2'.split(' '))
        fib = open('fib', 'rb')
        fib2 = open('fib2', 'rb')
        self.assertEqual(ord(fib2.read(1)), 0x0)
        self.assertEqual(ord(fib2.read(1)), 0x0)
        self.assertEqual(ord(fib2.read(1)), 0x0)
        self.assertEqual(ord(fib2.read(1)), 0x0)
        fib.read(4)
        self.assertEqual(fib.read(), fib2.read())
        fib.close()
        fib2.close()

    def test_args(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 Z1W 5 5'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)

    def test_overlap(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 -w 2 Z1W 0 Z1W 1-10'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)

    def test_range(self):
        faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 -w 2 Z1W 0x0-0xF'.split(' '))
        fib = open('fib', 'rb')
        fib2 = open('fib2', 'rb')
        for _ in range(16):
            fib.read(1)
            self.assertEqual(ord(fib2.read(1)), 0x0)
        self.assertEqual(fib.read(), fib2.read())
        fib.close()
        fib2.close()

    def test_no_w(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 Z1W 0'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)

    def test_no_multiple(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 -w 4 Z1W 0-8'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)
