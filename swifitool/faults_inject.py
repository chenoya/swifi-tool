import argparse
import shutil
import sys
import os


def check_or_fail(condition, msg):
    """Assert that the condition holds and if not exit with the error message.

    :param condition: the boolean cndition
    :param msg: the message printed on stderr
    """
    if not condition:
        sys.stderr.write(msg + "\n")
        exit(-1)


def set_bytes(outfile, start_addr, value=0, nb_repeat=1):
    """Write a 8-bit value several times in a file starting at a specified offset.

    :param outfile: the IO stream of the file
    :param start_addr: the offset in the file
    :param value: the byte value as an integer 0-255
    :param nb_repeat: number of repetitions
    """
    outfile.seek(start_addr)
    outfile.write(bytes([value] * nb_repeat))


# def set_bit(outfile, addr, significance, value):
#     check_or_fail(0 <= significance < 8, "The significance of the bit must be between 0 and 7 : " + str(significance))
#     check_or_fail(value == 0 or value == 1, "The value is not binary : " + str(value))
#     outfile.seek(addr)
#     prev_value = ord(outfile.read(1))
#     if value == 0:
#         prev_value &= ~(1 << significance)
#     else:
#         prev_value |= (1 << significance)
#     set_bytes(outfile, addr, prev_value)


def bits_list(bytes_l):
    """Transform a list of byte offsets to a list of bit offsets.

    :param bytes_l: list of offsets (integer)
    :return: a list
    """
    bits_l = []
    for i in bytes_l:
        bits_l.extend(range(i * 8, i * 8 + 8))
    return bits_l


def parse_addr(addr):
    """Parse a string representing an address or a range of addresses to an list of integer address(es).
    Exit with error if format is wrong.

    :param addr: the string to parse
    :return: a list of adresses
    """
    try:
        return [int(addr, 0)]
    except ValueError:
        borders = addr.split('-')
        try:
            check_or_fail(len(borders) == 2, "Wrong address format : " + addr)
            ret = list(range(int(borders[0], 0), int(borders[1], 0) + 1))  # inclusive borders
            check_or_fail(len(ret) > 0, "Address range empty : " + addr)
            return ret
        except ValueError:
            check_or_fail(False, "Wrong address format : " + addr)


class ExecConfig:
    """Keeps the configuration variables."""

    def __init__(self, infile, outfile, arch, word_length):
        super().__init__()
        self.infile = infile
        self.outfile = outfile
        self.arch = arch
        self.word_length = word_length


class FaultModel:
    """A fault model with its characteristics and behavior."""
    name = ""
    docs = ""
    nb_args = 0

    def __init__(self, config):
        super().__init__()
        self.config = config

    def edited_memory_locations(self):
        """Returns the locations of the bits edited by the fault model."""

    def apply(self, opened_file):
        """Apply the fault model to the given file."""


class FLP(FaultModel):
    name = 'FLP'
    docs = '    FLP addr significance \t flip one specific bit'
    nb_args = 2

    def __init__(self, config, args):
        super().__init__(config)
        self.addr = parse_addr(args[0])
        check_or_fail(len(self.addr) == 1, "FLP does not support address range")
        try:
            self.significance = int(args[1], 0)
            check_or_fail(0 <= self.significance < 8,
                          "Significance must be between 0 and 7 : " + str(self.significance))
        except ValueError:
            check_or_fail(False, "Wrong significance format : " + args[1])

    def edited_memory_locations(self):
        return [self.addr[0] * 8 + self.significance]

    def apply(self, opened_file):
        opened_file.seek(self.addr[0])
        prev_value = ord(opened_file.read(1))
        prev_value ^= (1 << self.significance)
        set_bytes(opened_file, self.addr[0], prev_value)


class Z1B(FaultModel):
    name = 'Z1B'
    docs = '    Z1B addr \t\t\t set one byte to 0x0'
    nb_args = 1

    def __init__(self, config, args):
        super().__init__(config)
        self.addr = parse_addr(args[0])

    def edited_memory_locations(self):
        return bits_list(self.addr)

    def apply(self, opened_file):
        set_bytes(opened_file, self.addr[0], nb_repeat=len(self.addr))


class Z1W(FaultModel):
    name = 'Z1W'
    docs = '    Z1W addr \t\t\t set one word to 0x0'
    nb_args = 1

    def __init__(self, config, args):
        super().__init__(config)
        self.addr = parse_addr(args[0])
        check_or_fail(config.word_length is not None, "Word size required when using Z1W")
        check_or_fail(len(self.addr) == 1 or len(self.addr) % config.word_length == 0,
                      "Range of addresses for Z1W must be multiple of the word length")

    def edited_memory_locations(self):
        if len(self.addr) == 1:
            return bits_list(range(self.addr[0], self.addr[0] + self.config.word_length))
        else:
            return bits_list(self.addr)

    def apply(self, opened_file):
        if len(self.addr) == 1:
            set_bytes(opened_file, self.addr[0], nb_repeat=self.config.word_length)
        else:
            set_bytes(opened_file, self.addr[0], nb_repeat=len(self.addr))


class NOP(FaultModel):
    name = 'NOP'
    docs = '    NOP addr \t\t\t nop one address (1 or 2 bytes depending on arch)'
    nb_args = 1

    def __init__(self, config, args):
        super().__init__(config)
        self.addr = parse_addr(args[0])
        check_or_fail(config.arch is not None, "Architecture required when using NOP")
        if self.config.arch == 'arm' and len(self.addr) != 1:
            check_or_fail(len(self.addr) % 2 == 0, "Range of addresses for NOP must be multiple of two on ARM")

    def edited_memory_locations(self):
        if len(self.addr) == 1:
            if self.config.arch == 'x86':
                return bits_list(self.addr)
            else:
                return bits_list(range(self.addr[0], self.addr[0] + 2))
        else:
            return bits_list(self.addr)

    def apply(self, opened_file):
        if self.config.arch == 'x86':
            set_bytes(opened_file, self.addr[0], 0x90, nb_repeat=len(self.addr))
        else:
            if len(self.addr) == 1:
                set_bytes(opened_file, self.addr[0], 0b00000000)
                set_bytes(opened_file, self.addr[0] + 1, 0b10111111)
            else:
                for i in range(len(self.addr) // 2):
                    set_bytes(opened_file, self.addr[0] + 2 * i, 0b00000000)
                    set_bytes(opened_file, self.addr[0] + 2 * i + 1, 0b10111111)


class JMP(FaultModel):
    name = 'JMP'
    docs = '    JMP addr target \t\t change the jump to point on the target'
    nb_args = 2

    def __init__(self, config, args):
        super().__init__(config)
        self.addr = parse_addr(args[0])
        check_or_fail(len(self.addr) == 1, "Range of addresses not supported with JMP")
        check_or_fail(config.arch is not None, "Architecture required when using JMP")
        absolute_target = None
        try:
            absolute_target = int(args[1], 0)
        except ValueError:
            check_or_fail(False, "Invalid target for JMP : " + args[1])
        check_or_fail(0 <= absolute_target < os.stat(config.infile).st_size, "Target outside the file")
        f = open(self.config.infile, 'rb')
        f.seek(self.addr[0])
        b0 = ord(f.read(1))
        b1 = ord(f.read(1))
        if b0 == 0xEB:
            self.target = absolute_target - (self.addr[0] + 1 + 1)
            check_or_fail(self.config.arch == 'x86', "Opcode 0xEB only supported with x86")
            check_or_fail(-2 ** 7 <= self.target < 2 ** 7, "Target value out of range : " + str(self.target))
            self.type = 0
        elif b0 == 0xE9:
            try:
                f.seek(self.addr[0] - 1)
                b_prev = ord(f.read(1))
            except ValueError:
                b_prev = 0
            if b_prev == 0x66:
                self.addr = [self.addr[0] - 1]
                self.target = absolute_target - (self.addr[0] + 2 + 2)
                check_or_fail(self.config.arch == 'x86', "Opcode 0x66 0xE9 only supported with x86")
                check_or_fail(-2 ** 15 <= self.target < 2 ** 15, "Target value out of range : " + str(self.target))
                self.type = 2
            else:
                self.target = absolute_target - (self.addr[0] + 1 + 4)
                check_or_fail(self.config.arch == 'x86', "Opcode 0xE9 only supported with x86")
                check_or_fail(-2 ** 31 <= self.target < 2 ** 31, "Target value out of range : " + str(self.target))
                self.type = 1
        elif b0 == 0x66 and b1 == 0xE9:
            self.target = absolute_target - (self.addr[0] + 2 + 2)
            check_or_fail(self.config.arch == 'x86', "Opcode 0x66 0xE9 only supported with x86")
            check_or_fail(-2 ** 15 <= self.target < 2 ** 15, "Target value out of range : " + str(self.target))
            self.type = 2
        else:
            check_or_fail(False, "Unknow opcode at JMP address : " + hex(b0))
        f.close()

    def edited_memory_locations(self):
        if self.type == 0:
            return bits_list(range(self.addr[0] + 1, self.addr[0] + 2))
        elif self.type == 1:
            return bits_list(range(self.addr[0] + 1, self.addr[0] + 5))
        elif self.type == 2:
            return bits_list(range(self.addr[0] + 2, self.addr[0] + 4))

    def apply(self, opened_file):
        if self.type == 0:
            opened_file.seek(self.addr[0] + 1)
            opened_file.write(bytes([self.target & 0xFF]))
        elif self.type == 1:
            opened_file.seek(self.addr[0] + 1)
            opened_file.write(bytes([self.target & 0xFF]))
            opened_file.write(bytes([self.target >> 8 & 0xFF]))
            opened_file.write(bytes([self.target >> 16 & 0xFF]))
            opened_file.write(bytes([self.target >> 24 & 0xFF]))
        elif self.type == 2:
            opened_file.seek(self.addr[0] + 2)
            opened_file.write(bytes([self.target & 0xFF]))
            opened_file.write(bytes([self.target >> 8 & 0xFF]))


class JBE(FaultModel):
    name = 'JBE'
    docs = '    JBE addr target \t\t change the conditional jump to point on the target'
    nb_args = 2

    def __init__(self, config, args):
        super().__init__(config)
        self.addr = parse_addr(args[0])
        check_or_fail(len(self.addr) == 1, "Range of addresses not supported with JBE")
        check_or_fail(config.arch is not None, "Architecture required when using JBE")
        absolute_target = None
        try:
            absolute_target = int(args[1], 0)
        except ValueError:
            check_or_fail(False, "Invalid target for JBE : " + args[1])
        check_or_fail(0 <= absolute_target < os.stat(config.infile).st_size, "Target outside the file")
        f = open(self.config.infile, 'rb')
        f.seek(self.addr[0])
        b0 = ord(f.read(1))
        b1 = ord(f.read(1))
        b2 = ord(f.read(1))
        if 0x70 <= b0 <= 0x7F or b0 == 0xE3:  # there might be a prefix 0x67 before 0xE3
            self.target = absolute_target - (self.addr[0] + 1 + 1)
            check_or_fail(self.config.arch == 'x86', "Opcode " + hex(b0) + " only supported with x86")
            check_or_fail(-2 ** 7 <= self.target < 2 ** 7, "Target value out of range : " + str(self.target))
            self.type = 0
        elif b0 == 0x0F and 0x80 <= b1 <= 0x8F:
            try:
                f.seek(self.addr[0] - 1)
                b_prev = ord(f.read(1))
            except ValueError:
                b_prev = 0
            if b_prev == 0x66:
                self.addr = [self.addr[0] - 1]
                self.target = absolute_target - (self.addr[0] + 3 + 2)
                check_or_fail(self.config.arch == 'x86', "Opcode 0x66 " + hex(b0) + " only supported with x86")
                check_or_fail(-2 ** 15 <= self.target < 2 ** 15, "Target value out of range : " + str(self.target))
                self.type = 2
            else:
                self.target = absolute_target - (self.addr[0] + 2 + 4)
                check_or_fail(self.config.arch == 'x86', "Opcode " + hex(b0) + " only supported with x86")
                check_or_fail(-2 ** 31 <= self.target < 2 ** 31, "Target value out of range : " + str(self.target))
                self.type = 1
        elif b0 == 0x66 and b1 == 0x0F and 0x80 <= b2 <= 0x8F:
            self.target = absolute_target - (self.addr[0] + 3 + 2)
            check_or_fail(self.config.arch == 'x86', "Opcode 0x66 " + hex(b0) + " only supported with x86")
            check_or_fail(-2 ** 15 <= self.target < 2 ** 15, "Target value out of range : " + str(self.target))
            self.type = 2
        else:
            check_or_fail(False, "Unknow opcode at JBE address : " + hex(b0))
        f.close()

    def edited_memory_locations(self):
        if self.type == 0:
            return bits_list(range(self.addr[0] + 1, self.addr[0] + 2))
        elif self.type == 1:
            return bits_list(range(self.addr[0] + 2, self.addr[0] + 6))
        elif self.type == 2:
            return bits_list(range(self.addr[0] + 3, self.addr[0] + 5))

    def apply(self, opened_file):
        if self.type == 0:
            opened_file.seek(self.addr[0] + 1)
            opened_file.write(bytes([self.target & 0xFF]))
        elif self.type == 1:
            opened_file.seek(self.addr[0] + 2)
            opened_file.write(bytes([self.target & 0xFF]))
            opened_file.write(bytes([self.target >> 8 & 0xFF]))
            opened_file.write(bytes([self.target >> 16 & 0xFF]))
            opened_file.write(bytes([self.target >> 24 & 0xFF]))
        elif self.type == 2:
            opened_file.seek(self.addr[0] + 3)
            opened_file.write(bytes([self.target & 0xFF]))
            opened_file.write(bytes([self.target >> 8 & 0xFF]))


def main(argv):
    fault_models = {'FLP': FLP, 'Z1B': Z1B, 'Z1W': Z1W, 'NOP': NOP, 'JMP': JMP, 'JBE': JBE}

    # Collect parameters
    parser = argparse.ArgumentParser(description='Software implemented fault injection tool',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', '--infile', type=str, metavar='INFILE', required=True, help='path to the source file')
    parser.add_argument('-o', '--outfile', type=str, metavar='OUTFILE', required=True,
                        help='path to the destination file')
    parser.add_argument('-w', '--wordsize', type=int, metavar='WORDSIZE', required=False,
                        help='number of bytes in a word')
    parser.add_argument('-a', '--arch', type=str, metavar='ARCHITECTURE', required=False, choices=['x86', 'arm'],
                        help='architecture of the executable (x86 or arm)')
    parser.add_argument('-g', '--graphical', action='store_true', required=False,
                        help='open a window comparing the input and the output')
    parser.add_argument('-f', '--fromfile', type=str, metavar='FILE_MODELS', required=False,
                        help='read the faults models from a file instead of command line')
    parser.add_argument('fault_models', nargs='*', metavar='FAULT_MODEL',
                        help='one fault model followed by its parameters\n' +
                             'The possible models are :\n' + "\n".join([s.docs for s in fault_models.values()]) +
                             '\naddr can be a number or a range (number-number)')
    args = parser.parse_args(argv[1:])
    check_or_fail(args.wordsize is None or args.wordsize > 0, "Word size must be positive")

    # General configuration
    config = ExecConfig(os.path.expanduser(args.infile), os.path.expanduser(args.outfile), args.arch, args.wordsize)

    # Fault models asked
    if args.fromfile is not None:
        with open(args.fromfile, 'r') as ff:
            args.fault_models.extend(ff.read().split())
    check_or_fail(len(args.fault_models) >= 1, "No fault models provided")
    fm_list = []
    indices = [i for i, x in enumerate(args.fault_models) if fault_models.get(x) is not None]
    indices.append(len(args.fault_models))

    for i in range(len(indices) - 1):
        n = indices[i]
        fm_name = args.fault_models[n]
        fm_type = fault_models.get(fm_name)
        if fm_type is not None:
            check_or_fail(indices[i + 1] - n - 1 == fm_type.nb_args, "Wrong number of parameters for " + fm_name)
            ar = []
            for j in range(fm_type.nb_args):
                ar.append(args.fault_models[n + 1 + j])
            fm_list.append(fm_type(config, ar))

    # Check that the faults do not overlap and do not write outside the end of the file
    mem = {}
    max_bits = os.stat(config.infile).st_size * 8
    for f in fm_list:
        for m in f.edited_memory_locations():
            check_or_fail(0 <= m < max_bits, "Address outside file content : byte " + hex(m // 8))
            check_or_fail(mem.get(m) is None, "Applying two fault models at the same place : byte " + hex(m // 8))
            mem[m] = f.name

    # Duplicate the input and then apply the faults
    shutil.copy(config.infile, config.outfile)
    with open(config.outfile, "r+b") as file:
        for f in fm_list:
            f.apply(file)

    # Open a window for comparing the Input/Output with the faults highlighted
    if args.graphical:
        colors = {'FLP': 'turquoise', 'Z1B': 'green', 'Z1W': 'green2', 'NOP': 'red', 'JMP': 'orange', 'JBE': 'tomato'}
        import diff_ui
        diff_ui.diff_ui(config.infile, config.outfile, fm_list, colors)


if __name__ == '__main__':
    main(sys.argv)
