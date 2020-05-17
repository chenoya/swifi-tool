class ExecConfig:
    """Keeps the configuration variables."""

    def __init__(self, infile, outfile, arch, word_length):
        super().__init__()
        self.infile = infile
        self.outfile = outfile
        self.arch = arch
        self.word_length = word_length