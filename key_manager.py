from Crypto.Cipher import DES3
from random import randint, choice
from binascii import unhexlify
from konfig import Config
import resp_gen
import logging
import shutil
import os
import re


def gen_key_field(field_48, field_41):
    global TERMINAL
    TERMINAL = field_41.decode('utf-8')

    if go_to_key_files():
        parsed = parse_key_pack(field_48)
        if(INI_KEYS['KLK']['CV'] == parsed[b'KLK']['DF22'].decode('utf-8') and
                (int(INI_KEYS['KLK']['INDEX']) == int(parsed[b'KLK']['DF20'].decode('utf-8')) or len(INI_KEYS) == 1)):

            res = gen_keys(['KLK', 'TAMK', 'TPMK', 'TMK', 'TAK', 'TPK', 'TDK'])
            create_new_key_file(int(INI_KEYS['KLK']['INDEX']) + 1)
            return res
        else:
            if len(INI_KEYS) == 1: gen_new_ini_file()
            return b''
    else:
        return b''


def create_new_key_file(index):
    with open(os.path.join(os.getcwd(), 'keys', ''.join([TERMINAL, '.ini'])), 'w') as file:
        file.write('[KEYS]\n')
        for key in KEYS:
            file.write(f'{key}={KEYS[key]["BODY"]}|{KEYS[key]["KCV"]}|{index}\n')


def parse_key_pack(data):
    def get_pack_dict(pack):
        tag_dict = dict()
        tag_info = pack.split(b'\xdf')
        if tag_info[0][1] == len(pack[2:]):
            tag_info.pop(0)
            for tag in tag_info:
                if tag[1] == len(tag[2:]):
                    tag_dict.update({f'DF{hex(tag[0]).replace("0x", "")}': tag[2:]})
                else:
                    resp_gen.set_logging()
                    logging.error(f'ERROR: missing data in tag: DF{hex(tag[0]).replace("0x", "")}\nPack:{pack}')
        else:
            resp_gen.set_logging()
            logging.error(f'ERROR: missing data in package №{tag_info[0][0]}\nPack:{pack}')
        return tag_dict

    res_dict = dict()
    packs = data.split(b'\xff')[1:]
    for p in packs:
        tmp_dict = get_pack_dict(p)
        try:
            res_dict.update({tmp_dict['DF24']: tmp_dict})
        except KeyError:
            resp_gen.set_logging()
            logging.error(f'ERROR: missing tag DF24 in package №{p[0]}\nPack:{p}')
    return res_dict


def get_string(bytes_data):
    res = list()
    for by in bytes_data:
        tmp = hex(by).replace('0x', '')
        if len(tmp) < 2:
            tmp = ''.join(['0', tmp])
        res.append(tmp)
    return ''.join(res)


def get_bytes(text):
    res = list()
    if len(text) % 2 != 0:
        text = ''.join(['0', text])
    for i in range(len(text) // 2):
        res.append(int(text[i*2:i*2+2], 16))
    return bytes(res)


def gen_keys(key_list):
    global KEYS
    KEYS = dict()
    pack_num = 1
    key_dict = dict()
    pack_list = list()
    index = str(int(INI_KEYS['KLK']['INDEX']) + 1).zfill(2).encode('utf-8')
    for key in key_list:
        key_value = ''.join([hex(randint(0, 15)).replace('0x', '').upper() for i in range(32)])
        crypto_key = DES3.new(unhexlify(key_value), DES3.MODE_ECB)
        key_dict.update({key: key_value})

        DF24 = b''.join([b'\xdf\x24', get_bytes(hex(len(key.encode('utf-8'))).replace('0x', '')), key.encode('utf-8')])
        DF40 = b'\xdf\x40\x01\x31'
        DF22 = b''.join([b'\xdf\x22\x06', crypto_key.encrypt(unhexlify('0' * 32)).hex().upper()[:6].encode('utf-8')])
        DF23 = b'\xdf\x23\x01\x54'
        DF28 = b''
        DF41 = b''

        DF20 = b''.join([b'\xdf\x20', get_bytes(hex(len(index)).replace('0x', '')), index])
        DF25 = b'\xdf\x25\x02\x30\x34'
        res_list = [DF24, DF40, DF22, DF23, DF20]
        if key == 'KLK':
            enc_key = DES3.new(unhexlify(INI_KEYS['KLK']['BODY']), DES3.MODE_ECB)
            DF41 = b''.join([b'\xdf\x41\x20', enc_key.encrypt(unhexlify(key_value)).hex().upper().encode('utf-8')])

            DF28 = b'\xdf\x28\x03KLK'
            DF25 = b'\xdf\x25\x02\x30\x30'
            DF29 = b'\xdf\x29\x02\x30\x30'
            res_list.append(DF29)
        elif key == 'TAK':
            enc_key = DES3.new(unhexlify(key_dict['TAMK']), DES3.MODE_ECB)
            DF41 = b''.join([b'\xdf\x41\x20', enc_key.encrypt(unhexlify(key_value)).hex().upper().encode('utf-8')])

            DF28 = b'\xdf\x28\x04TAMK'
        elif key == 'TPK':
            enc_key = DES3.new(unhexlify(key_dict['TPMK']), DES3.MODE_ECB)
            DF41 = b''.join([b'\xdf\x41\x20', enc_key.encrypt(unhexlify(key_value)).hex().upper().encode('utf-8')])

            DF28 = b'\xdf\x28\x04TPMK'
        elif key == 'TDK':
            enc_key = DES3.new(unhexlify(key_dict['TMK']), DES3.MODE_ECB)
            DF41 = b''.join([b'\xdf\x41\x20', enc_key.encrypt(unhexlify(key_value)).hex().upper().encode('utf-8')])

            DF28 = b'\xdf\x28\x03TMK'
        elif key == 'TAMK' or key == 'TPMK' or key == 'TMK':
            enc_key = DES3.new(unhexlify(key_dict['KLK']), DES3.MODE_ECB)
            DF41 = b''.join([b'\xdf\x41\x20', enc_key.encrypt(unhexlify(key_value)).hex().upper().encode('utf-8')])

            DF28 = b'\xdf\x28\x03KLK'
        res_list.extend([DF28, DF41, DF25])

        result = b''.join([b'\xff', get_bytes(str(pack_num)), get_bytes(hex(len(b''.join(res_list))).replace('0x', '')), b''.join(res_list)])
        pack_list.append(result)
        pack_num += 1
        KEYS.update({key: {'BODY': key_value, 'KCV': DF22[3:].decode('utf-8')}})
    return b''.join(pack_list)


def go_to_key_files():
    global INI_KEYS
    INI_KEYS = dict()
    if os.path.exists('keys'):
        file = None
        for term_file in os.listdir('keys'):
            if '.ini' in term_file:
                if ''.join([TERMINAL, '.ini']) == term_file:
                    file = os.path.join('keys', term_file)
                elif ''.join(['NEW_', TERMINAL, '.ini']) == term_file:
                    try:
                        new_conf = Config(os.path.join('keys', term_file)).as_args()
                        comp_1 = new_conf[new_conf.index('--KLK-Component-1') + 1].zfill(32).upper()
                        comp_2 = new_conf[new_conf.index('--KLK-Component-2') + 1].zfill(32).upper()
                        if(not re.match(r'[\dABCDEF]{32}', comp_1) or not re.match(r'[\dABCDEF]{32}', comp_2) or
                                comp_1 == '0' * 32 and comp_2 == '0' * 32):
                            raise ValueError
                        new_klk = DES3.new(unhexlify(klk_compile(comp_1, comp_2)), DES3.MODE_ECB)
                        klk_cv = new_klk.encrypt(unhexlify('0' * 32)).hex().upper()[:6]
                        os.remove(os.path.join(os.getcwd(), 'keys', term_file))
                        INI_KEYS.update({'KLK': {
                            'BODY': klk_compile(comp_1, comp_2),
                            'CV': klk_cv,
                            'INDEX': '0'
                        }})
                        return True
                    except ValueError:
                        print(f'Wrong values in {term_file}, please try again.\n')
            else:
                try:
                    os.remove(os.path.join(os.getcwd(), 'keys', term_file))
                except PermissionError:
                    shutil.rmtree(os.path.join(os.getcwd(), 'keys', term_file), ignore_errors=True)
        if file:
            try:
                conf_vals = Config(file).as_args()
                for i in range(len(conf_vals) // 2):
                    key_vals = conf_vals[i*2+1].split('|')
                    if((not re.match(r'[\dABCDEF]{32}', key_vals[0]) or len(key_vals[0]) != 32) or
                       (not re.match(r'[\dABCDEF]{6}', key_vals[1]) or len(key_vals[1]) != 6) or
                        not re.match(r'\d+', key_vals[2])): raise IndexError
                    INI_KEYS.update({conf_vals[i*2].split('-')[-1]: {
                        'BODY': key_vals[0],
                        'CV': key_vals[1],
                        'INDEX': key_vals[2]
                    }})
                if INI_KEYS:
                    return True
                return False
            except IndexError:
                resp_gen.set_logging()
                logging.error(f'Error while parsing file {file}')
                return False
        else:
            gen_new_ini_file()
            return False
    else:
        os.mkdir('keys')
        return go_to_key_files()


def gen_new_ini_file():
    file_name = os.path.join(os.getcwd(), 'keys', ''.join(['NEW_', TERMINAL, '.ini']))
    with open(file_name, 'w') as new_file:
        new_file.write('[KLK]\nComponent_1=\nComponent_2=')
    print(f'New card acceptor terminal!To create new KLK go to -\n{file_name}\n')


def klk_compile(comp_1, comp_2):
    def hex_splitter(klk):
        template = re.compile('.{2}')
        return re.findall(template, klk)
    comp_1 = hex_splitter(comp_1)
    comp_2 = hex_splitter(comp_2)
    comp_klk = str()
    for i in range(16):
        temp = hex(int(comp_1[i], 16) ^ int(comp_2[i], 16)).replace('0x', '')
        if len(temp) < 2: temp = '0' + temp
        comp_klk += temp.upper()
    return comp_klk
