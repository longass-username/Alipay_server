from random import randint, choice
from konfig import Config
from time import sleep
import datetime
import logging
import socket
import sys
import os
import re


def form_answer(request, rc_dict, status_ready=True):
    def gen_check_val(data):
        lrc = 0
        for symbol in data:
            lrc ^= symbol
        return chr(lrc)

    def gen_trans_id():
        time = datetime.datetime.now()
        time = str(time.time()).split(':')
        trans_id = time[0] + time[1] + ''.join(time[2].split('.'))[:4]
        return trans_id

    def sale_qr_answer():
        pattern = re.compile(r'\x02.{45}')

        RC = '001'
        rrn = gen_trans_id()
        const_fields = re.search(pattern, request)[0]
        qr_code = 'g<QR:https://example.com>'
        approval_code = ''.join(['F', ''.join([str(randint(0, 9)) for i in range(6)]), ' A'])
        try:
            card_type = ''.join(['R', field_dict['Field <R>']])
            sequence_number = ''.join([field_dict['Field <h>'][:-1], '0'])
            optional_data = f'a&C{field_dict["Subfield <C>"]}#&R01#&r{rrn}#&p{rrn}#'

            if 'NULL' in approval_code: raise KeyError
        except KeyError:
            return reverse_answer()

        response = '\x1c'.join([const_fields + RC, approval_code, card_type, optional_data, qr_code, sequence_number,
                                't' + rrn]) + b'\x03'.decode('utf-8')
        response += gen_check_val(response.encode('utf-8')[1:])
        return response.encode('utf-8')

    def sale_status_answer():
        pattern = re.compile(r'\x02.{45}')

        if status_ready:
            if rc_dict['sale_rc']:
                RC = '001'
                alipay_status = "g<ALIPAY_STATUS:SUCCESS>"
            else:
                RC = '602'
                alipay_status = "g<ALIPAY_STATUS:FAILED>"
        else:
            RC = '601'
            alipay_status = "g<ALIPAY_STATUS:UNKNOW>"

        rrn = gen_trans_id()
        const_fields = re.search(pattern, request)[0]
        card_type = 'RD'
        sequence_number = ''.join([field_dict['Field <h>'][:-1], '0'])
        optional_data = f'a&C{field_dict["Subfield <C>"]}#&R01#&r{rrn}#&p{rrn}#'

        response = '\x1c'.join([const_fields + RC, card_type, optional_data, alipay_status, sequence_number,
                                't' + rrn]) + b'\x03'.decode('utf-8')
        response += gen_check_val(response.encode('utf-8')[1:])
        return response.encode('utf-8')

    def sale_final_answer():
        pattern = re.compile(r'\x02.{45}')

        RC = '001'
        rrn = gen_trans_id()
        const_fields = re.search(pattern, request)[0]
        approval_code = ''.join(['F', ''.join([str(randint(0, 9)) for i in range(6)]), ' A'])
        try:
            card_type = ''.join(['R', field_dict['Field <R>']])
            sequence_number = ''.join([field_dict['Field <h>'][:-1], '0'])
            optional_data = f'a&C{field_dict["Subfield <C>"]}#&R01#&r{rrn}#&p{rrn}#'
        except KeyError:
            return reverse_answer()

        response = '\x1c'.join([const_fields + RC, approval_code, card_type, optional_data, sequence_number,
                                't' + rrn]) + b'\x03'.decode('utf-8')
        response += gen_check_val(response.encode('utf-8')[1:])
        return response.encode('utf-8')

    def refund_answer():
        pattern = re.compile(r'\x02.{45}')

        rrn = gen_trans_id()
        RC = rc_dict['refund_rc']
        const_fields = re.search(pattern, request)[0]
        card_type = 'RD'
        sequence_number = ''.join([field_dict['Field <h>'][:-1], '0'])
        approval_code = ''.join(['F', ''.join([str(randint(0, 9)) for i in range(6)]), ' A'])

        try: optional_data = f'a&C{field_dict["Subfield <C>"]}#&R01#&r{rrn}#&p{rrn}#'
        except KeyError: return reverse_answer()

        response = '\x1c'.join([const_fields + RC, approval_code, card_type, optional_data, sequence_number,
                                't' + rrn]) + b'\x03'.decode('utf-8')
        response += gen_check_val(response.encode('utf-8')[1:])
        return response.encode('utf-8')

    def reverse_answer():
        pattern = re.compile(r'\x02.{45}')

        RC = rc_dict['void_rc']
        const_fields = re.search(pattern, request)[0]
        response = ''.join([const_fields, RC]) + b'\x03'.decode('utf-8')
        response += gen_check_val(response.encode('utf-8')[1:])
        return response.encode('utf-8')

    def close_batch_answer():
        def get_rand_val(val):
            op_num = str(randint(1, 99))
            rand = randint(4, 6)
            return ''.join([''.join(['0' * (4 - len(op_num)), op_num]),
                            choice(['+', '-']),
                            ''.join(['0' * (val - rand), ''.join([str(randint(0, 9)) for i in range(rand)])])])

        RC = '007'
        pattern = re.compile(r'\x02.{45}')
        lom_pattern = re.compile(r'\x1c([lom].+)\x03')
        const_fields = re.search(pattern, request)[0]
        try:
            lom_fields = str(re.search(lom_pattern, request).group(1))
        except AttributeError:
            response = ''.join([const_fields, '898']) + b'\x03'.decode('utf-8')
            response += gen_check_val(response.encode('utf-8')[1:])
            return response.encode('utf-8')

        h_key = 'H' + ''.join([choice([choice(['A', 'B', 'C', 'D', 'E', 'F']), str(randint(0, 9))]) for i in range(32)])
        m_key = 'M' + ''.join([choice([choice(['A', 'B', 'C', 'D', 'E', 'F']), str(randint(0, 9))]) for i in range(32)])

        if lom_fields[0] == 'l':
            num = str(int(lom_fields[1:7]) + 1)
            lom_fields = 'l' + '0' * (6 - len(num)) + num + lom_fields[7:]
        elif lom_fields[0] == 'o':
            num = str(int(lom_fields[1:4]) + 1)
            lom_fields = 'o' + '0' * (3 - len(num)) + num + lom_fields[4:]

        if not rc_dict['cl_batch']:
            res = ''.join([get_rand_val(18) for i in range(3)])
            lom_fields = ''.join([lom_fields[:7], res])

        if request[41:43] == '62':
            response = '\x1c'.join([const_fields + RC, h_key, m_key, lom_fields]) + b'\x03'.decode('utf-8')
            response += gen_check_val(response.encode('utf-8')[1:])
            return response.encode('utf-8')
        else:
            response = '\x1c'.join([const_fields + RC, lom_fields]) + b'\x03'.decode('utf-8')
            response += gen_check_val(response.encode('utf-8')[1:])
            return response.encode('utf-8')

    if len(request) >= 49:
        try:
            field_dict = parse_data(request)
            if request[41:43] == '00':
                return reverse_answer()
            elif request[41:43] == '01':
                return sale_qr_answer()
            elif request[41:43] == '02':
                return sale_final_answer()
            elif request[41:43] == '04':
                return refund_answer()
            elif request[41:43] == '36':
                return sale_status_answer()
            elif request[41:43] == '60' or request[41:43] == '61' or request[41:43] == '62':
                return close_batch_answer()
            else:
                return None
        except TypeError as e:
            set_logging(); logging.error(f'ERROR:\n{e}')
            return None
    else:
        return b'\x04'  # <EOT>


def print_hex_dump(tptp_str):
    if tptp_str:
        result = ''
        hex_dump = []
        for i in tptp_str:
            if len(hex(i)) == 3:
                hex_dump.append(hex(i).replace('0x', '0'))
            else:
                hex_dump.append(hex(i).replace('0x', ''))

        counter = 1
        for symbol in hex_dump:
            if counter == 8:
                result += ' '
            elif counter == 16:
                counter = 1
                result += '\n'

            result += symbol + ' '
            counter += 1
        result += '\n'
        set_logging(); logging.info(f'HEX DUMP:\n{result}')
        return result


def parse_data(req):
    if len(req) < 48: return None
    try: req = req.encode('utf-8')
    except AttributeError: pass

    req = req[1:-2].split(b'\x1c')
    req = [r.decode('utf-8') for r in req]
    header = req.pop(0)
    res_dict = {
        'Device type': header[:2],
        'Transmission number': header[2:4],
        'Terminal ID': header[4:20],
        'Employee ID': header[20:26],
        'Current date': header[26:32],
        'Current time': header[32:38],
        'Message type': header[38:39],
        'Message sub type': header[39:40],
        'Transaction code': header[40:42],
        'Processing flag 1': header[42:43],
        'Processing flag 2': header[43:44],
        'Processing flag 3': header[44:45],
        'Response code': header[45:48]
    }
    if req:
        for field in req:
            res_dict.update({f'Field <{field[0]}>': field[1:]})

    if 'Field <a>' in res_dict:
        sub_res = dict()
        a_field = res_dict['Field <a>']
        template = re.compile(r'&(.+?)#')
        tmp = re.findall(template, a_field)
        for t in tmp:
            sub_res.update({f'Subfield <{t[0]}>': t[1:]})
        res_dict.update(sub_res)
    return res_dict


def print_result(values):
    for val in values:
        print('{:20}: {}'.format(val, values[val]))
    print('\n', end='')


def print_req_res(data):
    meta_symb = {
        b'\x01': b'<SOH>',
        b'\x02': b'<STX>',
        b'\x03': b'<ETX>',
        b'\x04': b'<EOT>',
        b'\x05': b'<ENQ>',
        b'\x06': b'<ACK>',
        b'\x15': b'<NAK>',
        b'\x1c': b'<FS>',
        b'\x0d': b'<CR>',
        b'\x1d': b'<GS>'
    }
    if data:
        for symbol in meta_symb:
            if symbol in data:
                data = data.replace(symbol, meta_symb[symbol])
        if b'<ETX>' in data:
            data = data[:-1] + b'<LRC>'
        return data.decode('utf-8')
    else:
        return None


def conf_parser():
    if not os.path.exists('config.ini'):
        file = open('config.ini', 'w')
        file.write('[Srv_settings]\n'
                   f'SERVER_ADDRESS={str(socket.gethostbyname_ex(socket.gethostname())[2][0])}\n'
                   'SERVER_PORT=\n'
                   'PROTOCOL=TPTP\n'
                   'HEX_DUMP=0\n'
                   'PARSE=0\n\n'
                   '[Tptp_settings]\n'
                   'STATUS=1\n'
                   'CLOSE_BATCH=1\n'
                   'PROCESS_TIME=0\n'
                   'REFUND_RC=001\n'
                   'VOID_RC=001\n\n'
                   '[Own_settings]\n'
                   'KEY_DECLINE_RC=01\n'
                   'CLOSE_BATCH=1\n'
                   'PROCESS_TIME=0\n'
                   'REFUND_RC=00\n'
                   'SALE_RC=00\n\n'
                   '[DELAY]\n'
                   'VOID_DELAY=0\n'
                   'FINAL_DELAY=0\n'
                   'STATUS_DELAY=0\n'
                   'REFUND_DELAY=0\n'
                   'QR_CODE_DELAY=0\n'
                   'DEFAULT_DELAY=0\n'
                   'CLOSE_OP_DELAY=0\n')
        file.close()

    conf = Config('config.ini')
    try:
        sett_dict = {
            'parse': conf.as_args()[conf.as_args().index('--Srv-settings-PARSE') + 1],
            'hexd': conf.as_args()[conf.as_args().index('--Srv-settings-HEX-DUMP') + 1],
            'port': conf.as_args()[conf.as_args().index('--Srv-settings-SERVER-PORT') + 1],
            'protocol': conf.as_args()[conf.as_args().index('--Srv-settings-PROTOCOL') + 1],
            'addr': conf.as_args()[conf.as_args().index('--Srv-settings-SERVER-ADDRESS') + 1],
            'tptp_stat_time': conf.as_args()[conf.as_args().index('--Tptp-settings-PROCESS-TIME') + 1],
            'tptp_cl_batch': conf.as_args()[conf.as_args().index('--Tptp-settings-CLOSE-BATCH') + 1],
            'refund_rc': conf.as_args()[conf.as_args().index('--Tptp-settings-REFUND-RC') + 1],
            'void_rc': conf.as_args()[conf.as_args().index('--Tptp-settings-VOID-RC') + 1],
            'stat': conf.as_args()[conf.as_args().index('--Tptp-settings-STATUS') + 1],
            'key_decline_rc': conf.as_args()[conf.as_args().index('--Own-settings-KEY-DECLINE-RC') + 1],
            'own_stat_time': conf.as_args()[conf.as_args().index('--Own-settings-PROCESS-TIME') + 1],
            'own_cl_batch': conf.as_args()[conf.as_args().index('--Own-settings-CLOSE-BATCH') + 1],
            'own_refund_rc': conf.as_args()[conf.as_args().index('--Own-settings-REFUND-RC') + 1],
            'own_sale_rc': conf.as_args()[conf.as_args().index('--Own-settings-SALE-RC') + 1],
            'void_time': conf.as_args()[conf.as_args().index('--DELAY-VOID-DELAY') + 1],
            'final_time': conf.as_args()[conf.as_args().index('--DELAY-FINAL-DELAY') + 1],
            'status_time': conf.as_args()[conf.as_args().index('--DELAY-STATUS-DELAY') + 1],
            'refund_time': conf.as_args()[conf.as_args().index('--DELAY-REFUND-DELAY') + 1],
            'qr_code_time': conf.as_args()[conf.as_args().index('--DELAY-QR-CODE-DELAY') + 1],
            'default_time': conf.as_args()[conf.as_args().index('--DELAY-DEFAULT-DELAY') + 1],
            'close_op_time': conf.as_args()[conf.as_args().index('--DELAY-CLOSE-OP-DELAY') + 1]
        }

        set_logging(); logging.info(f'Config values:{sett_dict}')
        return sett_dict
    except ValueError:
        print('config.ini is damaged!')
        input('Press ENTER to exit.')
        sys.exit()


def check_log_files():
    try:
        log_list = os.listdir(os.path.join(os.getcwd(), 'logs'))

        count = 0
        MAX_FILES = 10
        for log in log_list:
            if '.log' in log:
                count += 1

        if count > MAX_FILES:
            sorted_list = []
            for logs in log_list:
                sorted_list.append(int(''.join(logs[:-4].split('-'))))
            sorted_list.sort()

            for j in range(len(log_list) - MAX_FILES):
                log_file = str(sorted_list.pop(0))
                log_file = '-'.join([log_file[:4], log_file[4:6], log_file[6:]]) + '.log'
                os.remove(os.path.join('logs', log_file))
    except Exception as e:
        set_logging(); logging.error(f'ERROR:\n{e}')
        sys.exit()


def set_logging():
    if not os.path.exists('logs'):
        os.mkdir('logs')

    logfile = f'{str(datetime.datetime.now().date())}.log'
    return logging.basicConfig(filename=f'logs/{logfile}',
                               filemode='a',
                               format=u'[%(filename)-12s][LINE:%(lineno)-4d][%(levelname)-8s][%(asctime)s] %(message)s',
                               datefmt='%H:%M:%S',
                               level=logging.DEBUG)
