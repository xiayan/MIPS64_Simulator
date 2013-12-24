from string import center
from os.path import expanduser
from CPU import *

def parseCommands(filename, int_regs, fp_regs, memory, used):
    filename = expanduser(filename)
    inFile = open(filename, 'r')
    cmdList = []
    mode = -1

    for line in inFile:
        l = line.strip().replace(",", "  ")
        if "I-REGISTERS" in l:
            mode = 0
            continue
        elif "FP-REGISTERS" in l:
            mode = 1
            continue
        elif "MEMORY" in l:
            mode = 2
            continue
        elif "CODE" in l:
            mode = 3
            continue

        if len(line.split()) < 2: continue # get rid of blank lines
        if mode == 0 or mode == 1:
            r, num = l.split() # r is the register name, num is the value
            r = eval(r[1:])
            num = eval(num)
            if mode == 0:
                int_regs[r].realVal = num
            elif mode == 1:
                fp_regs[r].realVal = (num + 0.0)
                used[r] = True
        elif mode == 2:
            r, num = l.split()
            r = eval(r)
            num = eval(num)
            memory[r] = (num + 0.0)
        elif mode == 3:
            segs = l.split()

            op = segs[0]
            if op == 'L.D':
                dest = eval(segs[1][1:])
                op1 = eval(segs[2].split('(')[1][1:-1])
                op2 = eval(segs[2].split('(')[0])
                cmdList.append(Command(0, (dest, op1, op2)))
                used[dest] = True
            elif op == 'S.D':
                dest = eval(segs[2][1:])
                op1 = eval(segs[1].split('(')[1][1:-1])
                op2 = eval(segs[1].split('(')[0])
                cmdList.append(Command(3, (dest, op1, op2)))
                used[dest] = True
            elif op == 'MUL.D' or op == 'ADD.D':
                dest = eval(segs[1][1:])
                op1 = eval(segs[2][1:])
                op2 = eval(segs[3][1:])
                if op == 'MUL.D':
                    cmdList.append(Command(1, (dest, op1, op2)))
                else:
                    cmdList.append(Command(2, (dest, op1, op2)))
                used[dest] = True

    return cmdList

def main():
    int_regs = [] # array of Integer registers
    fp_regs = []  # array of FP registers
    memory = {}
    used = [False] * 32

    # Add in 32 Int registers and FP registers
    for i in range(32):
        int_regs.append(Register())
        fp_regs.append(Register())

    filename = raw_input("Instruction Filename: ")
    cmdList = parseCommands(filename, int_regs, fp_regs, memory, used)

    # create a CPU simulator and run the commands
    cpu = CPU()
    timeString = cpu.simulate(cmdList, fp_regs, int_regs, memory)
    print 'Timing Table'
    print timeString

    # Output timing file
    timeFile = raw_input("Enter the filename for timing result: ")
    timeFile = expanduser(timeFile)
    if '.' not in timeFile: timeFile += '.txt' # append txt extenstion by default
    timeOutput = open(timeFile, 'w')
    timeOutput.write(timeString)
    timeOutput.close()

    # Only reports the registers that were used by the instructions
    registerResults = [(x, str(y.realVal)) for x, y in enumerate(fp_regs)
            if used[x] == True]

    # Set up width of fields in the output
    spacing = max([len(y) for x, y in registerResults]) + 2
    spacing = 5 if spacing < 5 else spacing

    registerTitle = ''.join(center('F' + str(x), spacing)
            for x, y in registerResults)
    registerContent = ''.join(center(y, spacing) for x, y in registerResults)
    print '\nRegister Results'
    print registerTitle
    print registerContent + '\n'

    # Output register file
    registerFile = raw_input("Enter the filename for register files: ")
    registerFile = expanduser(registerFile)
    if '.' not in registerFile: registerFile += '.txt'
    registerOutput = open(registerFile, 'w')
    registerOutput.write(registerTitle + '\n')
    registerOutput.write(registerContent + '\n')
    registerOutput.close()

main()

