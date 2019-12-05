from random import randint
from konfig import Config
from time import sleep
import datetime
import logging
import sys
import os
import re


def form_answer(request):
    def gen_check_val(data):
        lrc = 0
        for symbol in data:
            lrc ^= symbol
        return chr(lrc)

    def sale_qr_answer():
        pattern = re.compile(r'\x02.{45}')
        seq_pattern = re.compile(r'h\d{9}')

        RC = '001'
        card_type = 'RD'
        qr_code = 'g<QR:https://www.youtube.com/watch?v=dQw4w9WgXcQ>'
        rrn = ''.join([str(randint(0, 9)) for i in range(8)])
        const_fields = re.search(pattern, request)[0]
        approval_code = 'F' + ''.join([str(randint(0, 9)) for i in range(6)]) + ' A'
        optional_data = f'a&C643#&R01#&r{rrn}#&p{rrn}#'

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
        rrn_pattern = re.compile(r'T(\d{8})')
        seq_pattern = re.compile(r'h\d{9}')

        RC = '001'
        card_type = 'RD'
        rrn = re.search(rrn_pattern, request).group(1)
        optional_data = f'a&C643#&R01#&r{rrn}#&p{rrn}#'
        alipay_status = "g<ALIPAY_STATUS:SUCCESS>"
        const_fields = re.search(pattern, request)[0]
        sequence_number = re.search(seq_pattern, request)[0] + '0'

        response = '\x1c'.join([const_fields + RC, card_type, optional_data, alipay_status, sequence_number, 't' + rrn])
        response = response + b'\x03'.decode('utf-8')
        LRC = gen_check_val(response.encode('utf-8')[1:])
        response += LRC
        return response.encode('utf-8')

    def sale_final_answer():
        pattern = re.compile(r'\x02.{45}')

        RC = '001'
        const_fields = re.search(pattern, request)[0]

        response = const_fields + RC
        response = response + b'\x03'.decode('utf-8')
        LRC = gen_check_val(response.encode('utf-8')[1:])
        response += LRC
        return response.encode('utf-8')

    def refund_answer():
        pattern = re.compile(r'\x02.{45}')
        seq_pattern = re.compile(r'h\d{9}')
        rrn_pattern = re.compile(r't(\d{8})')

        RC = '001'
        card_type = 'RD'
        rrn = re.search(rrn_pattern, request).group(1)
        const_fields = re.search(pattern, request)[0]
        approval_code = 'F' + ''.join([str(randint(0, 9)) for i in range(6)]) + ' A'
        optional_data = f'a&C643#&R01#&r{rrn}#&p{rrn}#'
        sequence_number = re.search(seq_pattern, request)[0] + '0'

        response = '\x1c'.join([const_fields + RC, approval_code, card_type, optional_data, sequence_number, 't' + rrn])
        response = response + b'\x03'.decode('utf-8')
        LRC = gen_check_val(response.encode('utf-8')[1:])
        response += LRC
        return response.encode('utf-8')

    def reverse_answer():
        pattern = re.compile(r'\x02.{45}')
        rrn_pattern = re.compile(r't(\d{8})')

        try:
            rrn = re.search(rrn_pattern, request).group(1)
            optional_data = f'a&C643#&R01#&r{rrn}#&p{rrn}#'
        except TypeError:
            rrn = ''.join([str(randint(0, 9)) for i in range(8)])
            optional_data = f'a&C643#&R01#&r{rrn}#&p{rrn}#'

        RC = '001'
        const_fields = re.search(pattern, request)[0]

        response = '\x1c'.join([const_fields + RC, optional_data, 't' + rrn])

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
                   'SERVER_ADDRESS=\n'
                   'SERVER_PORT=\n'
                   'HEX_DUMP=\n\n'
                   '[Ali_settings]\n'
                   'RC=\n'
                   'TIME=')
        file.close()

    conf = Config('config.ini')
    try:
        sett_dict = {
            'addr': conf.as_args()[conf.as_args().index('--Srv-settings-SERVER-ADDRESS') + 1],
            'port': conf.as_args()[conf.as_args().index('--Srv-settings-SERVER-PORT') + 1],
            'resp': conf.as_args()[conf.as_args().index('--Ali-settings-RC') + 1],
            'time': conf.as_args()[conf.as_args().index('--Ali-settings-TIME') + 1],
            'hexd': conf.as_args()[conf.as_args().index('--Srv-settings-HEX-DUMP') + 1]
        }
        if len(sett_dict['resp']) < 3:
            sett_dict['resp'] = '0' * (3 - len(sett_dict['resp'])) + sett_dict['resp']

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
