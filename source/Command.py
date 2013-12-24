class Command(object):
    """Decode a MIPS64 command"""
    def __init__(self, opcode, ops):
        self._opcode = opcode
        self._ops = ops
        self._stallNum = 0
        self._bypassing = 0 # 0: no / 1: op1 / 2: op2 / 3: op1 and op2
        #Or for EXE 0: F1 real / 1: F1 bypass
        self._pipeType = 0

        if self._opcode == 1:
            self._pipeType = 1
        elif self._opcode == 2:
            self._pipeType = 2

        self._stage = 0

    @property
    def opcode(self):
        """read-only property opcode"""
        return self._opcode

    @property
    def ops(self):
        return self._ops

    @property
    def stallNum(self):
        return self._stallNum
    @stallNum.setter
    def stallNum(self, value):
        self._stallNum = value

    @property
    def bypassing(self):
        return self._bypassing
    @bypassing.setter
    def bypassing(self, value):
        self._bypassing = value

    @property
    def stage(self):
        return self._stage
    @stage.setter
    def stage(self, value):
        self._stage = value

    @property
    def pipeType(self):
        return self._pipeType

    def finished(self):
        if self._pipeType == 0:
            return self._stage == 5
        elif self._pipeType == 1:
            return self._stage == 8
        elif self._pipeType == 2:
            return self._stage == 6

