from unittest import TestCase

import faults_inject


class Test_FLP(TestCase):
    def test_one_flip(self):
        faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 FLP 0x0 5'.split(' '))
        fib = open('fib', 'rb')
        fib2 = open('fib2', 'rb')
        self.assertEqual(ord(fib.read(1)), ord(fib2.read(1)) ^ 0b00100000)
        self.assertEqual(fib.read(), fib2.read())
        fib.close()
        fib2.close()

    def test_two_flip(self):
        faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 FLP 0x0 5 FLP 0x0 3'.split(' '))
        fib = open('fib', 'rb')
        fib2 = open('fib2', 'rb')
        self.assertEqual(ord(fib.read(1)), ord(fib2.read(1)) ^ 0b00101000)
        self.assertEqual(fib.read(), fib2.read())
        fib.close()
        fib2.close()

    def test_args(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 FLP 0x0-0x10'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)

    def test_overlap(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 FLP 0x0 5 FLP 0x0 5'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)

    def test_range(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 FLP 0x0-0x10 5'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)

    def test_sign(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 FLP 0x0 -5'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)

    def test_sign_2(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 FLP 0x0 x'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)

    def test_wrong_addr(self):
        ok = False
        try:
            faults_inject.main('../swifitool/faults_inject.py -i fib -o fib2 FLP xx7x 0'.split(' '))
        except SystemExit:
            ok = True
        self.assertTrue(ok)
