from string import center
from Register import *
from Command import *

class CPU(object):
    def __init__(self):
        self._i_pipeline = ['IF', 'ID', 'EX', 'MEM', 'WB']
        self._m_pipeline = ['IF', 'ID', 'M1', 'M2', 'M3', \
                'M4', 'MEM', 'WB']
        self._a_pipeline = ['IF', 'ID', 'A1', 'A2', 'MEM', 'WB']

    def _configure(self, cc, s, e, cmdList, fp_regs, int_regs, memory):
        # Compute the stall numbers. Only consider RAW and WAW
        cmd = cmdList[e]
        dest, op1, op2 = cmd.ops
        if cmd.opcode == 0: # Load, No RAW
            # WAW
            if fp_regs[dest].status == 1:
                cmd.stallNum = fp_regs[dest].written - cc - 3
                # if cmd.stallNum < 0: cmd.stallNum = 0

        elif cmd.opcode == 3: # Store, No WAW
            # RAW
            if fp_regs[dest].status == 1:
                cmd.bypassing = 1
                cmd.stallNum = fp_regs[dest].ready - cc - 1
                # if cmd.stallNum < 0: cmd.stallNum = 0

        elif cmd.opcode == 1 or cmd.opcode == 2: # Mult or Add
            # RAW: Use numbers to encode the bypassing situations
            # Check the Command class for detail
            if fp_regs[op1].status == 1:
                cmd.bypassing = 1
                cmd.stallNum = fp_regs[op1].ready - cc - 1
            if fp_regs[op2].status == 1:
                cmd.bypassing += 2
                if cmd.stallNum < fp_regs[op2].ready - cc - 1:
                    cmd.stallNum = fp_regs[op2].ready - cc - 1
            # WAW
            if fp_regs[dest].status >= 1:
                offset = 4 if cmd.opcode == 2 else 5
                if cmd.stallNum < fp_regs[dest].written - cc - offset:
                    cmd.stallNum = fp_regs[dest].written - cc - offset

        if cmd.stallNum < 0: cmd.stallNum = 0

        # Avoid functional dependencies (Write in the same cycle)
        # Generate a list of written cycles of all the instructions
        # in the pipeline, except for 'S.D'
        cycles = [fp_regs[r.ops[0]].written for r in cmdList[s:e] \
                if not r.finished()
                if r.opcode != 3]

        # Calculate the written cycle for the current instruction
        expected_write = cc + cmd.stallNum
        if cmd.opcode == 0 or cmd.opcode == 3:
            expected_write += 4
        elif cmd.opcode == 1:
            expected_write += 7
        elif cmd.opcode == 2:
            expected_write += 5

        # Avoid writing in the same cycle
        while expected_write in cycles:
            cmd.stallNum += 1
            expected_write += 1

    def _executeStages(self, cc, s, e, cmdList, fp_regs, int_regs, memory):
        # Assign 0 to unspecified registers
        for i in range(s, e + 1):
            cmd = cmdList[i]
            if cmd.finished(): continue
            dest, op1, op2 = cmd.ops

            if cmd.opcode == 0: # Load
                if cmd.stage == 1: # ID
                    fp_regs[dest].status = 1 # lock the dest register
                    fp_regs[dest].written = cc + 3
                    fp_regs[dest].ready = cc + 2
                elif cmd.stage == 3: # MEM
                    address = int_regs[op1].realVal + op2
                    if address in memory.keys():
                        fp_regs[dest].bypassVal = memory[address]
                    else:
                        fp_regs[dest].bypassVal = 0.0
                elif cmd.stage == 4: # WB
                    fp_regs[dest].realVal = fp_regs[dest].bypassVal
                    fp_regs[dest].status = 0 # release the dest register

            elif cmd.opcode == 3: # Store
                if cmd.stage == 3: # MEM
                    address = int_regs[op1].realVal + op2
                    if cmd.bypassing == 0:
                        memory[address] = fp_regs[dest].realVal
                    else:
                        memory[address] = fp_regs[dest].bypassVal

            # Could potentially combine Mult and Add, but run out of time
            elif cmd.opcode == 1: # Mult
                if cmd.stage == 1: # ID
                    fp_regs[dest].status = 1
                    fp_regs[dest].written = cc + 6
                    fp_regs[dest].ready = cc + 4
                elif cmd.stage == 5: # M4
                    result = 0.0
                    if cmd.bypassing == 0:
                        result = fp_regs[op1].realVal * fp_regs[op2].realVal
                    elif cmd.bypassing == 1:
                        result = fp_regs[op1].bypassVal * fp_regs[op2].realVal
                    elif cmd.bypassing == 2:
                        result = fp_regs[op1].realVal * fp_regs[op2].bypassVal
                    else:
                        result = fp_regs[op1].bypassVal * fp_regs[op2].bypassVal
                    fp_regs[dest].bypassVal = result
                elif cmd.stage == 7: # WB
                    fp_regs[dest].realVal = fp_regs[dest].bypassVal
                    fp_regs[dest].status = 0

            elif cmd.opcode == 2: # Add
                if cmd.stage == 1: # ID
                    fp_regs[dest].status = 1
                    fp_regs[dest].written = cc + 4
                    fp_regs[dest].ready = cc + 2
                elif cmd.stage == 3: # A2
                    result = 0.0
                    if cmd.bypassing == 0:
                        result = fp_regs[op1].realVal + fp_regs[op2].realVal
                    elif cmd.bypassing == 1:
                        result = fp_regs[op1].bypassVal + fp_regs[op2].realVal
                    elif cmd.bypassing == 2:
                        result = fp_regs[op1].realVal + fp_regs[op2].bypassVal
                    else:
                        result = fp_regs[op1].bypassVal + fp_regs[op2].bypassVal
                    fp_regs[dest].bypassVal = result
                elif cmd.stage == 5: # WB
                    fp_regs[dest].realVal = fp_regs[dest].bypassVal
                    fp_regs[dest].status = 0

    def _printStages(self, cc, s, e, cmdList, stall, spacing):
        result = ''
        for i in range(s, e + 1):
            cmd = cmdList[i]
            pipeline = None
            if cmd.pipeType == 0 or cmd.pipeType == 3:
                pipeline = self._i_pipeline
            elif cmd.pipeType == 1:
                pipeline = self._m_pipeline
            else:
                pipeline = self._a_pipeline

            if cmd.stage == 0 and stall:
                # Print '**' to represent stall if entered IF stage
                result += center('**', spacing)
            else:
                if not cmd.finished():
                    result += center(pipeline[cmd.stage], spacing)
                else:
                    result += ' ' * spacing

        # Set up the leading spaces
        result = s * spacing * " " + result
        # Set up the clock cycle number
        result = " " * (3 - len(str(cc+1))) + 'c#' + str(cc+1) \
                + "  "   + result
        return result + '\n'

    def simulate(self, cmdList, fp_regs, int_regs, memory):
        timeString = ''
        spacing = len(str(len(cmdList))) + 4 # Set up the width for each field
        header = ' ' * 7
        for i in range(1, len(cmdList)+1):
            header += center('I#' + str(i), spacing)
        timeString += (header + '\n')

        cc = 0
        s, e = 0, 0 # start and end of the commands in pipeline
        self._configure(cc, s, e, cmdList, fp_regs, int_regs, memory)
        cmdList[0].stage = -1
        config = False # flag to control configure new instruction
        stall = False  # flag to control printing stall

        while True:
            for i in range(s, e + 1):
                cmd = cmdList[i]
                stall = False
                if cmd.stallNum >= 1:
                    cmd.stallNum -= 1
                    stall = True
                elif cmd.stallNum == 0 and not cmd.finished():
                    cmd.stage += 1

                # If the current instruction is at ID
                # Configure the next instruction
                if cmd.stage == 1:
                    if e < len(cmdList) - 1:
                        e += 1
                        config = True

                #only advance when the current front is finished
                if cmd.finished() and i == s and s < len(cmdList) - 1:
                    s += 1

            # If all instructions are finished, break
            if not False in [m.finished() for m in cmdList]: break
            self._executeStages(cc, s, e, cmdList, fp_regs, int_regs, memory)
            if config:
                config = False
                self._configure(cc, s, e, cmdList, fp_regs, int_regs, memory)
            timeString += self._printStages(cc, s, e, cmdList, stall, spacing)
            cc += 1

        return timeString

