from random import randint
from konfig import Config
from time import sleep
import datetime
import logging
import socket
import sys
import os
import re


def form_answer(request, rc_dict, main_dict, status_ready=True):
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
        seq_pattern = re.compile(r'h\d{9}')

        RC = '001'
        card_type = 'RD'
        qr_code = 'g<QR:https://www.youtube.com/watch?v=dQw4w9WgXcQ>'
        rrn = gen_trans_id()
        const_fields = re.search(pattern, request)[0]
        approval_code = 'F' + ''.join([str(randint(0, 9)) for i in range(6)]) + ' A'
        optional_data = f'a&C{main_dict["currency"]}#&R01#&r{rrn}#&p{rrn}#'
        try:
            sequence_number = re.search(seq_pattern, request)[0] + '0'
        except TypeError:
            return reverse_answer()

        response = '\x1c'.join([const_fields + RC, approval_code, card_type, optional_data, qr_code, sequence_number, 't' + rrn])
        response = response + b'\x03'.decode('utf-8')
        LRC = gen_check_val(response.encode('utf-8')[1:])
        response += LRC
        return response.encode('utf-8')

    def sale_status_answer():
        pattern = re.compile(r'\x02.{45}')
        seq_pattern = re.compile(r'h\d{9}')

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

        card_type = 'RD'
        rrn = gen_trans_id()
        optional_data = f'a&C{main_dict["currency"]}#&R01#&r{rrn}#&p{rrn}#'
        const_fields = re.search(pattern, request)[0]
        sequence_number = re.search(seq_pattern, request)[0] + '0'

        response = '\x1c'.join([const_fields + RC, card_type, optional_data, alipay_status, sequence_number, 't' + rrn])
        response = response + b'\x03'.decode('utf-8')
        LRC = gen_check_val(response.encode('utf-8')[1:])
        response += LRC
        return response.encode('utf-8')

    def sale_final_answer():
        pattern = re.compile(r'\x02.{45}')
        seq_pattern = re.compile(r'h\d{9}')
        app_code_pattern = re.compile(r'F\d{6}\sA')

        RC = '001'
        card_type = 'RD'
        rrn = gen_trans_id()
        const_fields = re.search(pattern, request)[0]
        optional_data = f'a&C{main_dict["currency"]}#&R01#&r{rrn}#&p{rrn}#'
        app_code = re.search(app_code_pattern, request)[0]

        try:
            sequence_number = re.search(seq_pattern, request)[0] + '0'
        except TypeError:
            return reverse_answer()

        response = '\x1c'.join([const_fields + RC, app_code, card_type, optional_data, sequence_number, 't' + rrn])
        response = response + b'\x03'.decode('utf-8')
        LRC = gen_check_val(response.encode('utf-8')[1:])
        response += LRC
        return response.encode('utf-8')

    def refund_answer():
        pattern = re.compile(r'\x02.{45}')
        seq_pattern = re.compile(r'h\d{9}')

        RC = rc_dict['refund_rc']
        card_type = 'RD'
        rrn = gen_trans_id()
        const_fields = re.search(pattern, request)[0]
        approval_code = 'F' + ''.join([str(randint(0, 9)) for i in range(6)]) + ' A'
        optional_data = f'a&C{main_dict["currency"]}#&R01#&r{rrn}#&p{rrn}#'
        sequence_number = re.search(seq_pattern, request)[0] + '0'

        response = '\x1c'.join([const_fields + RC, approval_code, card_type, optional_data, sequence_number, 't' + rrn])
        response = response + b'\x03'.decode('utf-8')
        LRC = gen_check_val(response.encode('utf-8')[1:])
        response += LRC
        return response.encode('utf-8')

    def reverse_answer():
        pattern = re.compile(r'\x02.{45}')

        RC = rc_dict['void_rc']
        const_fields = re.search(pattern, request)[0]
        response = ''.join([const_fields, RC])
        response = response + b'\x03'.decode('utf-8')
        LRC = gen_check_val(response.encode('utf-8')[1:])
        response += LRC
        return response.encode('utf-8')

    if len(request) >= 49:
        try:
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
                   'HEX_DUMP=0\n\n'
                   '[Main_settings]\n'
                   'TERMINAL=12345678\n'
                   'CURRENCY=643\n\n'
                   '[Tptp_settings]\n'
                   'STATUS=1\n'
                   'PROCESS_TIME=0\n'
                   'REFUND_RC=001\n'
                   'VOID_RC=001\n\n'
                   '[Own_settings]\n'
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
            'hexd': conf.as_args()[conf.as_args().index('--Srv-settings-HEX-DUMP') + 1],
            'port': conf.as_args()[conf.as_args().index('--Srv-settings-SERVER-PORT') + 1],
            'protocol': conf.as_args()[conf.as_args().index('--Srv-settings-PROTOCOL') + 1],
            'addr': conf.as_args()[conf.as_args().index('--Srv-settings-SERVER-ADDRESS') + 1],
            'terminal': conf.as_args()[conf.as_args().index('--Main-settings-TERMINAL') + 1],
            'currency': conf.as_args()[conf.as_args().index('--Main-settings-CURRENCY') + 1],
            'tptp_stat_time': conf.as_args()[conf.as_args().index('--Tptp-settings-PROCESS-TIME') + 1],
            'refund_rc': conf.as_args()[conf.as_args().index('--Tptp-settings-REFUND-RC') + 1],
            'void_rc': conf.as_args()[conf.as_args().index('--Tptp-settings-VOID-RC') + 1],
            'stat': conf.as_args()[conf.as_args().index('--Tptp-settings-STATUS') + 1],
            'own_stat_time': conf.as_args()[conf.as_args().index('--Own-settings-PROCESS-TIME') + 1],
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
