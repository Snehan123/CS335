#!/usr/bin/env python
import sys
from get_reg import *
from utilities import *

class CodeGenerator:
    def gen_data_section(self):
        print("extern printf\n")
        print("section\t.data\n")
        print("print_int:\tdb\t\"%d\",10,0")
        for symbol in symbol_table.keys():
            if symbol_table[symbol].array_size != None:
                print(str(symbol) + "\ttimes\t" + str(symbol_table[symbol].array_size) + "\tdd\t0")
            else:
                print(str(symbol) + "\tdd\t0")

    def gen_start_template(self):
        print()
        print("section .text")
        print("\tglobal main")
        print("main:")

    def op_print_int(self, instr):
        print("\tpush ebp")
        print("\tmov ebp,esp")
        loc = get_best_location(instr.inp1)
        print("\tpush dword " + str(loc))
        print("\tpush dword print_int")
        print("\tcall printf")
        print("\tadd esp, 8")
        print("\tmov esp, ebp")
        print("\tpop ebp")

    def op_add(self, instr):
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", " + get_best_location(instr.inp1))
        R2 = get_best_location(instr.inp2)
        print("\tadd " + R1 + ", " + R2)
        update_reg_descriptors(R1,instr.out)
        free_regs(instr)


    def op_sub(self, instr):
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", " + get_best_location(instr.inp1))
        R2 = get_best_location(instr.inp2)
        print("\tsub " + R1 + ", " + R2)
        update_reg_descriptors(R1,instr.out)
        free_regs(instr)


    def op_mult(self, instr):
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", " + get_best_location(instr.inp1))
        flag = False        # to avoid multiple operations
        if instr.inp2.isdigit():
            if instr.inp2 == "2":
                print("\tshl " + R1 + ", 1")
                flag = True
            elif instr.inp2 == "4":
                print("\tshl " + R1 + ", 2")
                flag = True
        if not flag:
            R2 = get_best_location(instr.inp2)
            print("\timul " + R1 + ", " + R2)
        update_reg_descriptors(R1, instr.out)
        free_regs(instr)


    def op_div(self, instr):
        #1 thing that can be done is if inp1 is in eax then move it from reg so mov this after mov R1, eax
        save_reg_contents("edx")
        save_reg_contents("eax")
        print("\tmov eax, " + get_best_location(instr.inp1))
        print("\txor edx, edx")
        if instr.inp2.isdigit():
            R1, flag = get_reg(instr,exclude=["eax","edx"])
            print("\tmov " + R1 + ", " + get_best_location(instr.inp2))
            print("\tidiv " + R1)
        else:
            print("\tidiv dword " + get_best_location(instr.inp2))
        update_reg_descriptors("eax", instr.out)
        free_regs(instr)


    def op_modulo(self, instr):
        save_reg_contents("edx")
        save_reg_contents("eax")
        print("\txor edx, edx")
        print("\tmov eax, " + get_best_location(instr.inp1))
        if instr.inp2.isdigit():
            R1, flag = get_reg(instr,exclude=["eax","edx"])
            print("\tmov " + R1 + ", " + get_best_location(instr.inp2))
            print("\tidiv " + R1)
        else:
            print("\tidiv dword" + get_best_location(instr.inp2))

        update_reg_descriptors("edx", instr.out)
        free_regs(instr)


    def op_lshift(self, instr):
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", " + get_best_location(instr.inp1))
        R2 = get_best_location(instr.inp2)
        print("\tshl " + R1 + ", " + R2)
        update_reg_descriptors(R1, instr.out)
        free_regs(instr)


    def op_rshift(self, instr):
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", " + get_best_location(instr.inp1))
        R2 = get_best_location(instr.inp2)
        print("\tshr " + R1 + ", " + R2)
        update_reg_descriptors(R1, instr.out)
        free_regs(instr)


    def op_assign(self, instr):
        if instr.array_index_i1 == None and instr.array_index_o == None and instr.inp1.isdigit():
            R1, flag = get_reg(instr, compulsory=False)
            print("\tmov " + R1 + ", " + get_best_location(instr.inp1))
            if R1 in reg_descriptor.keys():
                update_reg_descriptors(R1, instr.out)

        elif instr.array_index_i1 == None and instr.array_index_o == None:
            if len(symbol_table[instr.inp1].address_descriptor_reg) == 0:
                R1, flag = get_reg(instr)
                print("\tmov " + R1 +", " + get_best_location(instr.inp1))
                update_reg_descriptors(R1,instr.inp1)

            if len(symbol_table[instr.inp1].address_descriptor_reg):
                for regs in symbol_table[instr.out].address_descriptor_reg:
                    reg_descriptor[regs].remove(instr.out)
                symbol_table[instr.out].address_descriptor_reg.clear()
                symbol_table[instr.out].address_descriptor_reg = symbol_table[instr.inp1].address_descriptor_reg.copy()

                for reg in symbol_table[instr.out].address_descriptor_reg:
                    reg_descriptor[reg].add(instr.out)

                free_regs(instr)

        elif instr.array_index_i1 != None:
            assert len(symbol_table[instr.inp1].address_descriptor_reg) == 0
            R1, flag = get_reg(instr)
            print("\tmov " + R1 + ", " + get_best_location(instr.array_index_i1))
            print("\tshl " + R1 + ", 2")
            print("\tadd " + R1 + ", " + instr.inp1)
            print("\tmov " + R1 + ", [" + R1 + "]")
            update_reg_descriptors(R1, instr.out)

        else:
            index = instr.array_index_o
            R1 = None
            if is_valid_sym(index):
                if len(symbol_table[index].address_descriptor_reg) == 0:
                    R1, _ = get_reg(instr)
                    print("\tmov " + R1 + ", " + get_best_location(index))
                    update_reg_descriptors(R1, index)
                else:
                    R1 = get_best_location(index)

                inp_reg = R1
                if index != instr.inp1:
                    inp_reg, flag = get_reg(instr, exclude=[R1])
                    if flag:
                        print("\tmov " + inp_reg + ", " + get_best_location(instr.inp1))
                        update_reg_descriptors(inp_reg,instr.inp1)
                print("\tmov [" + instr.out + "," + R1 + "*4], " + inp_reg)
            else:
                index = 4 * int(index)
                inp_reg, flag = get_reg(instr)
                if flag:
                    print("\tmov " + inp_reg + ", " + get_best_location(instr.inp1))
                    update_reg_descriptors(inp_reg,instr.inp1)
                print("\tmov [" + instr.out + "+" + str(index) + "], " + inp_reg)


    def op_logical(self, instr):
        # TODO: logical &&, ||
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", [" + instr.inp1 + "]")
        R2 = get_best_location(instr.inp2)
        def log_op(x):
            return {
                    "&" : "and ",
                    "|" : "or ",
                    "^" : "xor ",
                    # remove the following 2 lines after TODO
                    "&&": "and ",
                    "||": "or ",
            }[x]
        if (instr.operation != "~" and instr.operation != "!"):
            print("\t" + log_op(instr.operation) + R1 + ", " + R2)
        else:
            print("\tnot " + R1)

    def op_unary(self, instr):
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", " + get_best_location(instr.inp1))
        if instr.operation == "!" or instr.operation == "~":
            print("\tnot "+ R1)
        elif instr.operation == "++":
            print("\tinc "+ R1)
        elif instr.operation == "--":
            print("\tdec "+ R1)
        update_reg_descriptors(R1,instr.out)
        free_regs(instr)

    def op_ifgoto(self, instr):
        inp1 = instr.inp1
        inp2 = instr.inp2
        out = None
        jmp_label = None
        if instr.jmp_to_line != None:
            jmp_label = "line_no_" + str(instr.jmp_to_line)
        else:
            jmp_label = instr.jmp_to_label

        operator = instr.operation
        if inp1.isdigit() and inp2.isdigit():
            save_context()
            if operator == "geq":
                if inp1 >= inp2:
                    print("\tjmp " + jmp_label)
            elif operator == "gt":
                if inp1 > inp2:
                    print("\tjmp " + jmp_label)
            elif operator == "leq":
                if inp1 <= inp2:
                    print("\tjmp " + jmp_label)
            elif operator == "lt":
                if inp1 < inp2:
                    print("\tjmp " + jmp_label)
            elif operator == "eq":
                if inp1 == inp2:
                    print("\tjmp " + jmp_label)
            elif operator == "neq":
                if inp1 != inp2:
                    print("\tjmp " + jmp_label)
            return

        R1 = get_best_location(inp1)
        R2 = get_best_location(inp2)
        if R1 in reg_descriptor.keys():
            print("\tcmp " + R1 + ", " + R2)
        elif R2 in reg_descriptor.keys():
            print("\tcmp " + R1 + ", " + R2)
        else:
            instr.out = inp1
            instr.inp1 = None
            R, flag = get_reg(instr)
            print("\tmov " + R + ", " + R1)
            update_reg_descriptors(R,inp1)
            print("\tcmp " + R + ", " + R2)

        save_context()
        if operator == "geq":
            print("\tjge " + jmp_label)
        elif operator == "gt":
            print("\tjg " + jmp_label)
        elif operator == "leq":
            print("\tjle " + jmp_label)
        elif operator == "lt":
            print("\tjl " + jmp_label)
        elif operator == "eq":
            print("\tje " + jmp_label)
        elif operator == "neq":
            print("\tjne " + jmp_label)

        free_regs(instr)


    def op_label(self, instr):
        print(instr.label_name + ":")

    def op_call_function(self, instr):
        save_context()
        print("\tcall " + instr.jmp_to_label)

    def op_return(self, instr):
        if instr.is_main_return:
            print("\tmov eax, 0")
        elif instr.out != None:
            save_reg_contents("eax")
            print("\tmov eax, " + get_best_location(instr.out))
        print("\tret")

    def gen_code(self, instr):
        '''
        Main function which calls other utility functions
        according to instruction type
        '''
        instr_type = instr.instr_type
        if instr.label_to_be_added == True:
            print("line_no_" + str(instr.line_no) + ":")

        if instr_type == "arithmetic":
            if instr.operation == "+":
                self.op_add(instr)
            elif instr.operation == "-":
                self.op_sub(instr)
            elif instr.operation == "*":
                self.op_mult(instr)
            elif instr.operation == "/":
                self.op_div(instr)
            elif instr.operation == "%":
                self.op_modulo(instr)
            elif instr.operation == "<<":
                self.op_lshift(instr)
            elif instr.operation == ">>"
                self.op_rshift(instr)

        elif instr_type == "logical":
            self.op_logical(instr)

        elif instr_type == "assignment":
            self.op_assign(instr)

        elif instr_type == "ifgoto":
            self.op_ifgoto(instr)

        elif instr_type == "return":
            self.op_return(instr)

        elif instr_type == "label":
            self.op_label(instr)

        elif instr_type == "func_call":
            self.op_call_function(instr)

        elif instr_type == "print_int":
            self.op_print_int(instr)

        elif instr_type == "unary":
            self.op_unary(instr)

###################################global generator############################
generator = CodeGenerator()
###################################global generator############################

def next_use(leader, IR_code):
    '''
    This function determines liveness and next
    use information for each statement in basic block by
    performing a backward pass

    Then, it generates assembly code for each basic block
    by making a forward pass

    Finally, it saves all register contents into memory and
    resets the liveness and next use info in symbol table.

    '''
    generator = CodeGenerator()
    for b_start in range(len(leader) -  1):
        # iterate through all basic blocks
        basic_block = IR_code[leader[b_start] - 1:leader[b_start + 1] - 1]
        # for x in basic_block:
            # print(x.line_no)
        # print()
        for instr in reversed(basic_block):
            if is_valid_sym(instr.out):
                instr.per_inst_next_use[instr.out].live = symbol_table[instr.out].live
                instr.per_inst_next_use[instr.out].next_use = symbol_table[instr.out].next_use

            if is_valid_sym(instr.inp1):
                instr.per_inst_next_use[instr.inp1].live = symbol_table[instr.inp1].live
                instr.per_inst_next_use[instr.inp1].next_use = symbol_table[instr.inp1].next_use

            if is_valid_sym(instr.inp2):
                instr.per_inst_next_use[instr.inp2].live = symbol_table[instr.inp2].live
                instr.per_inst_next_use[instr.inp2].next_use = symbol_table[instr.inp2].next_use

            if is_valid_sym(instr.out):
                symbol_table[instr.out].live = False
                symbol_table[instr.out].next_use = None

            if is_valid_sym(instr.inp1):
                symbol_table[instr.inp1].live = True
                symbol_table[instr.inp1].next_use = instr.line_no

            if is_valid_sym(instr.inp2):
                symbol_table[instr.inp2].live = True
                symbol_table[instr.inp2].next_use = instr.line_no

        for instr in basic_block:
            generator.gen_code(instr)
        save_context()
        reset_live_and_next_use()

if __name__ == "__main__":
    leader, IR_code = read_three_address_code(sys.argv[1])
    generator.gen_data_section()
    generator.gen_start_template()
    next_use(leader, IR_code)