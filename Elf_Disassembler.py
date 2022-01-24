import sys


"""
@author Trofimov Maxim (tg: @trofik00777)
"""


def bp(a):
    for i in range(0, len(a), 16):
        print(" ".join(a[i:i + 16]),
              ''.join(chr(int(j, 16)) for j in a[i:i + 16]))


def generate_dict_section_names(section):
    names = dict()

    current_name = ""
    offset = 0
    for b in section:
        if b == "00":
            names[offset] = current_name
            offset += len(current_name) + 1
            current_name = ""
        else:
            current_name += chr(int(b, 16))

    return names


def find_name_in_strtab(strtab, offset):
    name = ""
    for i in range(offset, len(strtab)):
        if strtab[i] == "00":
            return name
        name += chr(int(strtab[i], 16))
    return name


def generate_symtab(symtab, strtab):
    to_type = {
        '00': 'NOTYPE',
        '01': 'OBJECT',
        '02': 'FUNC',
        '03': 'SECTION',
        '04': 'FILE',
        '05': 'COMMON',
        '06': 'TLS',
        '07': 'NUM',
        '10': 'LOOS',
        '12': 'HIOS',
        '13': 'LOPROC',
        '15': 'HIPROC'
    }
    to_bind = {
        '00': 'LOCAL',
        '01': 'GLOBAL',
        '02': 'WEAK',
        '03': 'NUM',
        '10': 'LOOS',
        '12': 'HIOS',
        '13': 'LOPROC',
        '15': 'HIPROC'
    }
    to_visibility = {
        '00': 'DEFAULT',
        '01': 'INTERNAL',
        '02': 'HIDDEN',
        '03': 'PROTECTED'
    }
    to_index = {
        '0000': 'UNDEF',
        'ff00': 'BEFORE',
        'ff01': 'AFTER',
        # 'ff1f': 'HIPROC',
        # 'ff20': 'LOOS',
        # 'ff3f': 'HIOS',
        'fff1': 'ABS',
        'fff2': 'COMMON',
        'ffff': 'XINDEX'  # SHN_SPEC для диапазона
    }

    # print("%s %-15s %7s %-8s %-8s %-8s %6s %s" %
    #       ("Symbol", "Value", "Size", "Type", "Bind", "Vis", "Index", "Name"))
    gen_symtab = []

    for i in range(0, len(symtab), 16):
        st_name = find_name_in_strtab(strtab, int(''.join(reversed(symtab[i:i + 4])), 16))
        st_value = hex(int(''.join(reversed(symtab[i + 4:i + 8])), 16))
        st_size = int(''.join(reversed(symtab[i + 8:i + 12])), 16)
        st_info = bin(int(symtab[i + 12], 16))[2:].rjust(8, '0')
        st_other = symtab[i + 13]
        st_shndx = ''.join(reversed(symtab[i + 14:i + 16]))

        key_to_type = hex(int(st_info[-4:], 2))[2:].rjust(2, '0')
        if key_to_type in to_type:
            st_type = to_type[key_to_type]
        else:
            st_type = "UNKNOWN_TYPE"
        st_bind = to_bind.get(hex(int(st_info[:4], 2))[2:].rjust(2, '0'))
        st_visibility = to_visibility.get(hex(int(st_other[-2:], 16))[2:].rjust(2, '0'))
        key_to_index = hex(int(st_shndx, 16))[2:].rjust(4, '0')
        if key_to_index in to_index:
            st_index = to_index[key_to_index]
        else:
            if 0xff00 <= int(key_to_index, 16) <= 0xff1f:
                st_index = "SPEC_PROC"
            elif 0xff20 <= int(key_to_index, 16) <= 0xff3f:
                st_index = "SPEC_OS"
            elif 0xff00 <= int(key_to_index, 16):
                st_index = "RESERVED_INDEX"
            else:
                st_index = int(key_to_index, 16)

        gen_symtab.append((i >> 4, st_value[2:], st_size, st_type, st_bind, st_visibility, st_index, st_name))
        # print("[%4i] 0x%-15s %5i %-8s %-8s %-8s %6s %s" %
        #       (i >> 4, st_value[2:], st_size, st_type, st_bind, st_visibility, st_index, st_name))

    return gen_symtab


def convert_reg_names(rd):
    if rd == 0:
        rd = "zero"
    elif rd == 1:
        rd = "ra"
    elif rd == 2:
        rd = "sp"
    elif rd == 3:
        rd = "gp"
    elif rd == 4:
        rd = "tp"
    elif rd <= 7:
        rd = f"t{rd - 5}"
    elif rd <= 9:
        rd = f"s{rd - 8}"
    elif rd <= 17:
        rd = f"a{rd - 10}"
    elif rd <= 27:
        rd = f"s{rd - 16}"
    elif rd <= 31:
        rd = f"t{rd - 25}"

    return rd


def convert_reg_names_rvc(rd):
    # "000", "s0",
    # "001", "s1",
    # "010", "a0",
    # "011", "a1",
    # "100", "a2",
    # "101", "a3",
    # "110", "a4",
    # "111", "a5"
    match rd:
        case 0:
            return "s0"
        case 1:
            return "s1"
        case 2:
            return "a0"
        case 3:
            return "a1"
        case 4:
            return "a2"
        case 5:
            return "a3"
        case 6:
            return "a4"
        case 7:
            return "a5"
        case _:
            return ""


def make_new_address(address, imm, symtab, queue, commands):
    new_address = hex(address + imm)[2:]
    new_address_symtab = find_in_symtab_by_address(symtab, new_address, True)
    if imm > 0:
        queue.add(new_address)
    elif imm < 0:
        for ind in range(len(commands)):
            if commands[ind][1][0] == int(new_address, 16):
                if commands[ind][1][1] == "":
                    commands[ind][1][1] = new_address_symtab
    else:
        return new_address, new_address_symtab, False
    return new_address, new_address_symtab, True


def build_rvc_command(command, address, symtab, queue, commands):
    code1_0 = command[-2:]
    str_address = hex(address)[2:]
    match code1_0:
        case "00":
            code15_13 = command[-16:-13]
            match code15_13:
                case '000':
                    nzuimm = int(command[-11:-7] + command[-13:-11] + command[-6] + command[-7] + "00", 2)
                    rd = int(command[-5:-2], 2)
                    rd = convert_reg_names_rvc(rd)
                    name = "c.addi4spn"
                    return [ "%08x %10s %s %s, %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, "sp", nzuimm]]
                case '001':
                    uimm = int(command[-7:-5] + command[-13:-10] + "000", 2)
                    rd = int(command[-5:-2], 2)
                    rd = convert_reg_names_rvc(rd)
                    rs1 = int(command[-10:-7], 2)
                    rs1 = convert_reg_names_rvc(rs1)
                    name = "c.fld"
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, uimm, rs1]]
                case '010':
                    uimm = int(command[-6] + command[-13:-10] + command[-7] + "00", 2)
                    rd = int(command[-5:-2], 2)
                    rd = convert_reg_names_rvc(rd)
                    rs1 = int(command[-10:-7], 2)
                    rs1 = convert_reg_names_rvc(rs1)
                    name = "c.lw"
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, uimm, rs1]]
                case '011':
                    uimm = int(command[-6] + command[-13:-10] + command[-7] + "00", 2)
                    rd = int(command[-5:-2], 2)
                    rd = convert_reg_names_rvc(rd)
                    rs1 = int(command[-10:-7], 2)
                    rs1 = convert_reg_names_rvc(rs1)
                    name = "c.flw"
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, uimm, rs1]]
                case '101':
                    uimm = int(command[-7:-5] + command[-13:-10] + "000", 2)
                    rs2 = int(command[-5:-2], 2)
                    rs2 = convert_reg_names_rvc(rs2)
                    rs1 = int(command[-10:-7], 2)
                    rs1 = convert_reg_names_rvc(rs1)
                    name = "c.fsd"
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, rs2, uimm]]
                case '110':
                    uimm = int(command[-6] + command[-13:-10] + command[-7] + "00", 2)
                    rs2 = int(command[-5:-2], 2)
                    rs2 = convert_reg_names_rvc(rs2)
                    rs1 = int(command[-10:-7], 2)
                    rs1 = convert_reg_names_rvc(rs1)
                    name = "c.sw"
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, uimm, rs2]]
                case '111':
                    uimm = int(command[-6] + command[-13:-10] + command[-7] + "00", 2)
                    rs2 = int(command[-5:-2], 2)
                    rs2 = convert_reg_names_rvc(rs2)
                    rs1 = int(command[-10:-7], 2)
                    rs1 = convert_reg_names_rvc(rs1)
                    name = "c.fsw"
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, uimm, rs2]]
                case _:
                    commands.append(["%08x %10s %s", [address, "", "unknown_command".upper()]])
                    return
                    # assert 0 == 1, "RVC 00 commander Error!"
        case "01":
            code15_13 = command[-16:-13]
            match code15_13:
                case '000':
                    if command[-12:-7] == "00000":
                        name = "c.nop"
                        return [ "%08x %10s %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper()]]
                    else:
                        rs1 = int(command[-12:-7], 2)
                        rs1 = convert_reg_names(rs1)
                        nzimm = bin_to_int_with_sign(command[-13] + command[-7:-2])
                        name = "c.addi"
                        return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, nzimm]]
                case '001':
                    name = "c.jal"
                    imm = bin_to_int_with_sign(command[-13] + command[-9] + command[-11:-9] + command[-7] + command[-8] + command[-3] + command[-12] + command[-6:-3] + '0')
                    new_address, new_address_symtab, result = make_new_address(address, imm, symtab, queue, commands)

                    if not result:
                        commands.append(["%08x %10s %s %s 0x%08x %s",
                                         [address, new_address_symtab,
                                          name.upper(), imm, int(new_address, 16),
                                          new_address_symtab.rstrip(":")]])  # bug
                        return None

                    return [ "%08x %10s %s %s 0x%08x %s",
                             [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), imm, int(new_address, 16), new_address_symtab.rstrip(":")]]
                case '010':
                    name = "c.li"
                    rd = int(command[-12:-7], 2)
                    rd = convert_reg_names(rd)
                    imm = bin_to_int_with_sign(command[-13] + command[-7:-2])
                    return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, imm]]
                case '011':
                    rd = int(command[-12:-7], 2)
                    if rd == 2:
                        name = "c.addi16sp"
                        nzimm = bin_to_int_with_sign(command[-13] + command[-5:-3] + command[-6] + command[-3] + command[-7] + "0000")
                    else:
                        name = "c.lui"
                        nzimm = bin_to_int_with_sign(command[-13] + command[-7:-2] + "0" * 12)
                    return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), convert_reg_names(rd), nzimm]]
                case '100':
                    code11_10 = command[-12:-10]
                    match code11_10:
                        case '00':
                            nzuimm = int(command[-13] + command[-7:-2], 2)
                            rs1 = int(command[-10:-7], 2)
                            rs1 = convert_reg_names_rvc(rs1)
                            if nzuimm == 0:
                                name = "c.srli64"
                                return [ "%08x %10s %s %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1]]
                            else:
                                name = "c.srli"
                                return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, nzuimm]]
                        case '01':
                            nzuimm = int(command[-13] + command[-7:-2], 2)
                            rs1 = int(command[-10:-7], 2)
                            rs1 = convert_reg_names_rvc(rs1)
                            if nzuimm == 0:
                                name = "c.srai64"
                                return [ "%08x %10s %s %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1]]
                            else:
                                name = "c.srai"
                                return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, nzuimm]]
                        case '10':
                            imm = bin_to_int_with_sign(command[-13] + command[-7:-2], 2)
                            rs1 = int(command[-10:-7], 2)
                            rs1 = convert_reg_names_rvc(rs1)
                            name = "c.andi"
                            return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, imm]]
                        case '11':
                            rs1 = int(command[-10:-7], 2)
                            rs1 = convert_reg_names_rvc(rs1)
                            rs2 = int(command[-5:-2], 2)
                            rs2 = convert_reg_names_rvc(rs2)
                            code6_5 = command[-7:-5]
                            if command[-13] == '0':
                                match code6_5:
                                    case '00':
                                        name = "c.sub"
                                    case '01':
                                        name = "c.xor"
                                    case '10':
                                        name = "c.or"
                                    case '11':
                                        name = "c.and"
                                    case _:
                                        commands.append(["%08x %10s %s", [address, "", "unknown_command".upper()]])
                                        return
                                        # assert 0 == 1, "c.sub-c.and assertion"
                                return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, rs2]]
                            else:
                                match code6_5:
                                    case '00':
                                        name = "c.subw"
                                    case '01':
                                        name = "c.addw"
                                    case '10' | '11':
                                        name = "reserved"
                                        return [ "%08x %10s %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper()]]
                                    case _:
                                        commands.append(["%08x %10s %s", [address, "", "unknown_command".upper()]])
                                        return
                                        # assert 0 == 1, "c.subw,c.addw assertion"
                                return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, rs2]]
                        case _:
                            commands.append(["%08x %10s %s", [address, "", "unknown_command".upper()]])
                            return
                            # assert 0 == 1, "RVC 100 assertion"
                case '101':
                    name = "c.j"
                    imm = bin_to_int_with_sign(command[-13] + command[-9] + command[-11:-9] + command[-7] + command[-8] + command[-3] + command[-12] + command[-6:-3] + '0', 2)
                    new_address, new_address_symtab, result = make_new_address(address, imm, symtab, queue, commands)

                    if not result:
                        commands.append(["%08x %10s %s %s 0x%08x %s",
                                         [address, new_address_symtab,
                                          name.upper(), imm, int(new_address, 16),
                                          new_address_symtab.rstrip(":")]])  # bug
                        return None

                    return [ "%08x %10s %s %s 0x%08x %s" ,
                             [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), imm, int(new_address, 16), new_address_symtab.rstrip(":")]]
                case '110':
                    name = "c.beqz"
                    rs1 = int(command[-10:-7], 2)
                    rs1 = convert_reg_names_rvc(rs1)
                    imm = bin_to_int_with_sign(command[-13] + command[-7:-5] + command[-3] + command[-12:-10] + command[-5:-3] + '0', 2)
                    new_address, new_address_symtab, result = make_new_address(address, imm, symtab, queue, commands)

                    if not result:
                        commands.append(["%08x %10s %s %s, %s 0x%08x %s",
                                         [address, new_address_symtab,
                                          name.upper(), rs1, imm, int(new_address, 16),
                                          new_address_symtab.rstrip(":")]])  # bug
                        return None

                    return [ "%08x %10s %s %s, %s 0x%08x %s" ,
                             [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, imm, int(new_address, 16), new_address_symtab.rstrip(":")]]
                case '111':
                    name = "c.bnez"
                    rs1 = int(command[-10:-7], 2)
                    rs1 = convert_reg_names_rvc(rs1)
                    imm = bin_to_int_with_sign(command[-13] + command[-7:-5] + command[-3] + command[-12:-10] + command[-5:-3] + '0', 2)
                    new_address, new_address_symtab, result = make_new_address(address, imm, symtab, queue, commands)

                    if not result:
                        commands.append(["%08x %10s %s %s, %s 0x%08x %s",
                                         [address, new_address_symtab,
                                          name.upper(), rs1, imm, int(new_address, 16),
                                          new_address_symtab.rstrip(":")]])  # bug
                        return None

                    return [ "%08x %10s %s %s, %s 0x%08x %s" ,
                             [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, imm, int(new_address, 16), new_address_symtab.rstrip(":")]]
                case _:
                    commands.append(["%08x %10s %s", [address, "", "unknown_command".upper()]])
                    return
                    # assert 0 == 1, "RVC 01 assertion Error!"
        case "10":
            code15_13 = command[-16:-13]
            rs1 = int(command[-12:-7], 2)
            rs1 = convert_reg_names(rs1)
            match code15_13:
                case '000':
                    nzuimm = int(command[-13] + command[-7:-2], 2)
                    if nzuimm == 0:
                        name = "c.slli64"
                        return [ "%08x %10s %s %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1]]
                    else:
                        name = "c.slli"
                        return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, nzuimm]]
                case '001':
                    name = "c.fldsp"
                    uimm = int(command[-5:-2] + command[-13] + command[-7:-5] + "000", 2)
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, uimm, "sp"]]
                case '010':
                    name = "c.lwsp"
                    uimm = int(command[-4:-2] + command[-13] + command[-7:-4] + "00", 2)
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, uimm, "sp"]]
                case '011':
                    name = "c.flwsp"
                    uimm = int(command[-4:-2] + command[-13] + command[-7:-4] + "00", 2)
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, uimm, "sp"]]
                case '100':
                    match command[-13]:
                        case '0':
                            rs2 = int(command[-7:-2], 2)
                            if rs2 == 0:
                                name = "c.jr"
                                return [ "%08x %10s %s %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1]]
                            else:
                                name = "c.mv"
                                rs2 = convert_reg_names(rs2)
                                return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, rs2]]
                        case '1':
                            if rs1 == "zero":
                                name = "c.ebreak"
                                return [ "%08x %10s %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper()]]
                            else:
                                rs2 = int(command[-7:-2], 2)
                                if rs2 == 0:
                                    name = "c.jalr"
                                    return [ "%08x %10s %s %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1]]
                                else:
                                    name = "c.add"
                                    rs2 = convert_reg_names(rs2)
                                    return [ "%08x %10s %s %s, %s" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, rs2]]
                        case _:
                            commands.append(["%08x %10s %s", [address, "", "unknown_command".upper()]])
                            return
                            # assert 0 == 1, "RVC 100 assert"
                case '101':
                    name = "c.fsdsp"
                    uimm = int(command[-10:-7] + command[-13:-10] + "000", 2)
                    rs2 = int(command[-7:-2], 2)
                    rs2 = convert_reg_names(rs2)
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs2, uimm, "sp"]]
                case '110':
                    name = "c.swsp"
                    uimm = int(command[-9:-7] + command[-13:-9] + "00", 2)
                    rs2 = int(command[-7:-2], 2)
                    rs2 = convert_reg_names(rs2)
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs2, uimm, "sp"]]
                case '111':
                    name = "c.fswsp"
                    uimm = int(command[-9:-7] + command[-13:-9] + "00", 2)
                    rs2 = int(command[-7:-2], 2)
                    rs2 = convert_reg_names(rs2)
                    return [ "%08x %10s %s %s, %s(%s)" , [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs2, uimm, "sp"]]
                case _:
                    commands.append(["%08x %10s %s", [address, "", "unknown_command".upper()]])
                    return
                    # assert 0 == 1, "RVC 10 assertion Error! Maybe"

        case _:
            commands.append(["%08x %10s %s", [address, "", "unknown_command".upper()]])
            return
            # assert 0 == 1, f"Incorrect RVC command {code1_0}"


def find_in_symtab_by_address(symtab, address, must=False):
    # result = []
    for i in symtab:
        if i[1] == address:
            if i[3] == "FUNC":
                # if i[2] != 0:  # but size==0?
                if i[-1] != "":
                    return i[-1]
                    # result.append(i[-1])
                else:
                    return "LOC_%05x" % int(address, 16)
                    # result.append("LOC_%05x" % int(address, 16))
    # if result == []:
    if must:
        return "LOC_%05x" % int(address, 16) + ":"
    return ""



def bin_to_int_with_sign(n, *ars):
    len_n = len(n) - 1
    result = (2**(len_n)) * (-int(n[0]))
    pos = 0
    step = 1
    while pos < len_n:
        result += step * int(n[-(pos + 1)])
        step *= 2
        pos += 1
    return result



def decode_commands(text, offset, symtab):
    rv32im = {
        '18': [
            'B',
            {
                '0': 'beq',
                '1': 'bne',
                '4': 'blt',
                '5': 'bge',
                '6': 'bltu',
                '7': 'bgeu'
            }
        ],
        '04': [
            'I',
            {
                '0': 'addi',
                '1': 'slli',
                '2': 'slti',
                '3': 'sltiu',
                '4': 'xori',
                '5': 'srli',
                '6': 'ori',
                '7': 'andi'
            }
        ],
        '0c': [
            'R',
            {
                '0': {
                    '0': 'add',
                    '1': 'sll',
                    '2': 'slt',
                    '3': 'sltu',
                    '4': 'xor',
                    '5': 'srl',
                    '6': 'or',
                    '7': 'and'
                },
                '32': {
                    '0': 'sub',
                    '5': 'sra'
                },
                # rv32m
                '1': {
                    '0': 'mul',
                    '1': 'mulh',
                    '2': 'mulhsu',
                    '3': 'mulhu',
                    '4': 'div',
                    '5': 'divu',
                    '6': 'rem',
                    '7': 'remu'
                }
            }

        ],
        '00': [
            'I',
            {
                '0': 'lb',
                '1': 'lh',
                '2': 'lw',
                '4': 'lbu',
                '5': 'lhu'
            }
        ],
        '08': [
            'S',
            {
                '0': 'sb',
                '1': 'sh',
                '2': 'sw'
            }
        ],
        '0d': [
            'U',
            'lui'
        ],
        '05': [
            'U',
            'auipc'
        ],
        '19': [
            'I',
            {
                '0': 'jalr'
            }
        ],
        '1b': [
            'J',
            'jal'
        ],
        '1c': [
            'I',
            {
                '0': ['ecall', 'ebreak'],
                '1': 'csrrw',
                '2': 'csrrs',
                '3': 'csrrc',
                '5': 'csrrwi',
                '6': 'csrrsi',
                '7': 'csrrci'
            }
        ]
    }

    commands = []

    index = 0
    queue = set()
    while index < len(text):
        command = bin(int(''.join(reversed(text[index:index + 4])), 16))[2:].rjust(32, '0')
        if command[-2:] != "11":
            command = bin(int(''.join(reversed(text[index:index + 2])), 16))[2:].rjust(16, '0')
            index += 2
            command_rvc = build_rvc_command(command, offset + index - 2, symtab, queue, commands)
            if command_rvc is not None:
                commands.append(command_rvc)
        else:
            index += 4
            code1_0 = command[-2:]
            code6_2 = hex(int(command[-7:-2], 2))[2:].rjust(2, '0')
            address = offset + index - 4
            str_address = hex(address)[2:]

            if code6_2 in rv32im:
                form, name = rv32im[code6_2]
                if isinstance(name, str):
                    pass
                else:
                    code14_12 = str(int(command[-15:-12], 2))
                    if code6_2 == "0c":
                        code31_25 = str(int(command[-32:-25], 2))
                        name = name[code31_25]
                        name = name[code14_12]
                    elif code6_2 == "1c":
                        name = name[code14_12]
                        if isinstance(name, list):
                            name = name[int(command[-21])]
                    else:
                        name = name[code14_12]
                if name == "srli":
                    if command[-31] == '1':
                        name = "srai"
            else:
                form = name = None


            match form:
                case 'R':
                    rd = int(command[-12:-7], 2)
                    rd = convert_reg_names(rd)
                    rs1 = int(command[-20:-15], 2)
                    rs1 = convert_reg_names(rs1)
                    rs2 = int(command[-25:-20], 2)
                    rs2 = convert_reg_names(rs2)
                    commands.append(["%08x %10s %s %s, %s, %s", [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, rs1, rs2]])
                case 'I':
                    rd = int(command[-12:-7], 2)
                    rd = convert_reg_names(rd)
                    rs1 = int(command[-20:-15], 2)
                    rs1 = convert_reg_names(rs1)
                    imm = bin_to_int_with_sign(command[-32:-20])
                    match name[0]:
                        case 'l' | 'j':
                            commands.append(["%08x %10s %s %s, %s(%s)", [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, imm, rs1]])
                        case 'e':
                            commands.append(["%08x %10s %s", [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper()]])
                        case _:
                            if name == "srai":
                                imm -= 1024
                            commands.append(["%08x %10s %s %s, %s, %s", [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, rs1, imm]])
                case 'S':
                    rs2 = int(command[-25:-20], 2)
                    rs2 = convert_reg_names(rs2)
                    rs1 = int(command[-20:-15], 2)
                    rs1 = convert_reg_names(rs1)
                    imm = bin_to_int_with_sign(command[-32:-25] + command[-12:-7])
                    commands.append(["%08x %10s %s %s, %s(%s)", [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs2, imm, rs1]]) # bug
                case 'B':
                    rs2 = int(command[-25:-20], 2)
                    rs2 = convert_reg_names(rs2)
                    rs1 = int(command[-20:-15], 2)
                    rs1 = convert_reg_names(rs1)
                    imm = bin_to_int_with_sign(command[-32] + command[-8] + command[-31:-25] + command[-12:-8] + '0')
                    new_address, new_address_symtab, result = make_new_address(address, imm, symtab, queue, commands)

                    if not result:
                        commands.append(["%08x %10s %s %s, %s, %s 0x%08x %s",
                                         [address, new_address_symtab,
                                          name.upper(), rs1, rs2, imm, int(new_address, 16), new_address_symtab.rstrip(":")]])  # bug
                        continue

                    commands.append(["%08x %10s %s %s, %s, %s 0x%08x %s",
                                     [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rs1, rs2, imm, int(new_address, 16), new_address_symtab.rstrip(":")]])
                case 'J':
                    rd = int(command[-12:-7], 2)
                    rd = convert_reg_names(rd)
                    imm = bin_to_int_with_sign(command[-32] + command[-20:-12] + command[-21] + command[-31:-21] + '0')
                    new_address, new_address_symtab, result = make_new_address(address, imm, symtab, queue, commands)

                    if not result:
                        commands.append(["%08x %10s %s %s, %s 0x%08x %s",
                                         [address, new_address_symtab,
                                          name.upper(), rd, imm, int(new_address, 16), new_address_symtab.rstrip(":")]])  # bug
                        continue

                    commands.append(["%08x %10s %s %s, %s 0x%08x %s",
                                     [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, imm, int(new_address, 16), new_address_symtab.rstrip(":")]])
                case 'U':
                    rd = int(command[-12:-7], 2)
                    rd = convert_reg_names(rd)
                    imm = bin_to_int_with_sign(command[-32:-12] + "0" * 12) # bug
                    commands.append(["%08x %10s %s %s, %s", [address, find_in_symtab_by_address(symtab, str_address, str_address in queue), name.upper(), rd, imm]])
                case _:
                    commands.append(["%08x %10s %s", [address, "", "unknown_command".upper()]])
                    # assert 0 == 1, "match-case assertion"

    return commands


def main(args=("test_elfRVC.elf", "out.txt"), log=False):
    filename = args[0]
    # assert filename.endswith(".elf"), "This format file not correct (It must be *.elf)"
    with open(filename, 'rb') as elf:
        test = elf.read()
        byte = [hex(i)[2:].rjust(2, '0') for i in test]

    assert byte[:7] == ['7f', '45', '4c', '46', '01', '01', '01'], "It's not correct elf file..."  # проверяем что это elf32 with little endian

    # e_entry = ''.join(reversed(byte[24:28]))
    e_phoff = ''.join(reversed(byte[28:32]))
    e_shoff = ''.join(reversed(byte[32:36]))
    e_phentsize = ''.join(reversed(byte[42:44]))
    e_shnum = int(''.join(reversed(byte[48:50])), 16)
    e_shstrndx = int(''.join(reversed(byte[50:52])), 16)



    section_header_table = byte[int(e_shoff, 16):]
    if log:
        print(test)
        print(byte)
        print(e_phoff, e_shoff, e_phentsize, '\n')
        bp(section_header_table)
        print()
        print(len(section_header_table) // 40)

    sh_offset_shrtrtab = int(''.join(reversed(section_header_table[40 * e_shstrndx + 16:40 * e_shstrndx + 16 + 4])), 16)
    sh_size_shrtrtab = int(''.join(reversed(section_header_table[40 * e_shstrndx + 20:40 * e_shstrndx + 20 + 4])), 16)

    section_names = byte[sh_offset_shrtrtab:sh_offset_shrtrtab + sh_size_shrtrtab]
    names = generate_dict_section_names(section_names)
    if log:
        print(names)
        bp(section_header_table)

    sections = dict()

    for index in range(e_shnum):
        sh_name = int(''.join(reversed(section_header_table[40 * index: 40 * index + 4])), 16)
        if log:
            print(f"{sh_name = }")
        name = names.get(sh_name)
        if name in [".text", ".symtab", ".strtab"]:
            sections[name] = dict()
            sections[name]["offset"] = int(''.join(reversed(section_header_table[40 * index + 16: 40 * index + 16 + 4])), 16)
            sections[name]["size"] = int(''.join(reversed(section_header_table[40 * index + 20: 40 * index + 20 + 4])), 16)
            sections[name]["address"] = int(''.join(reversed(section_header_table[40 * index + 12: 40 * index + 12 + 4])), 16)

    if log:
        print(sections)

    assert len(sections) == 3, "No such .text or .symtab"

    symtab = byte[sections[".symtab"]["offset"]:sections[".symtab"]["offset"] + sections[".symtab"]["size"]]
    if log:
        bp(symtab)
        print()

    text = byte[sections[".text"]["offset"]:sections[".text"]["offset"] + sections[".text"]["size"]]
    strtab = byte[sections[".strtab"]["offset"]:sections[".strtab"]["offset"] + sections[".strtab"]["size"]]

    del byte

    if log:
        bp(strtab)

        strtab_names = generate_dict_section_names(strtab)
        print(strtab_names)

        for i in range(0, len(symtab), 16):
            print(i, end=' ')
            print(find_name_in_strtab(strtab, int(''.join(reversed(symtab[i:i + 4])), 16)))

        print(hex(sections[".text"]["offset"]), hex(sections[".text"]["offset"] + sections[".text"]["size"]))
        print()
    generated_symtab = generate_symtab(symtab, strtab)
    commands = decode_commands(text, sections[".text"]["address"], generated_symtab)

    if log:
        print(*commands, sep='\n')

    with open(args[1], 'w', encoding="utf-8") as f:
        f.write(".text\n")
        for i in commands:
            f.write((i[0] % tuple(i[1])) + '\n')
        f.write('\n.symtab\n')
        f.write("%s %-15s %7s %-8s %-8s %-8s %6s %s\n" %
          ("Symbol", "Value", "Size", "Type", "Bind", "Vis", "Index", "Name"))
        for i in generated_symtab:
            f.write("[%4i] 0x%-15s %5i %-8s %-8s %-8s %6s %s\n" % i)
    return


if __name__ == "__main__":
    args = ["", ""]
    try:
        args = sys.argv
        assert len(args) > 2, "Number of args is less than 2"
        args = args[1:]
    except AssertionError as e:
        print(e)
        print("So enter names files now there:")
        args = input().split()
    except Exception as e:
        print(f"Error! Program arguments isn't correct. Try Again! (Error message: {e})")
        exit(0)

    try:
        main(args)
    except FileNotFoundError as fnfe:
        print("Error! Filename is incorrect! Exception message:", fnfe)
    except Exception as e:
        print("Other Error! Exception message:", e)
