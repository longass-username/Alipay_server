from binascii import unhexlify
from socket import socket
from select import select
import open_way
import resp_gen
import version
import logging
import time
import sys


def setup_vars():
    def get_rc():
        global VOID_RC
        global REFUND_RC
        global OWN_SALE_RC
        global OWN_REFUND_RC

        VOID_RC = str(int(config_dict['void_rc']))
        REFUND_RC = str(int(config_dict['refund_rc']))
        OWN_SALE_RC = str(int(config_dict['own_sale_rc'])).encode('utf-8')
        OWN_REFUND_RC = str(int(config_dict['own_refund_rc'])).encode('utf-8')

        if len(REFUND_RC) != 3:
            REFUND_RC = '0' * (3 - len(REFUND_RC)) + REFUND_RC
        if len(VOID_RC) != 3:
            VOID_RC = '0' * (3 - len(VOID_RC)) + VOID_RC
        if len(OWN_SALE_RC) != 2:
            OWN_SALE_RC = b'0' * (2 - len(OWN_SALE_RC)) + OWN_SALE_RC
        if len(OWN_REFUND_RC) != 2:
            OWN_REFUND_RC = b'0' * (2 - len(OWN_REFUND_RC)) + OWN_REFUND_RC

    global PARSE
    global TIMER
    global RC_DICT
    global PROTOCOL
    global MAIN_DICT
    global PRINT_HEX
    global INPUT_DATA
    global VOID_DELAY
    global OWN_RC_DICT
    global OUTPUT_DATA
    global FINAL_DELAY
    global SRV_ADDRESS
    global PROCESS_TIME
    global LAST_REQUEST
    global REFUND_DELAY
    global STATUS_DELAY
    global DEFAULT_DELAY
    global QR_CODE_DELAY
    global CLOSE_OP_DELAY
    global TIMER_CONN_LIST
    global OWN_PROCESS_TIME
    global STATUS_TIMER_LIST

    try:
        config_dict = resp_gen.conf_parser()  # converts config.ini into python dict
        get_rc()  # prepare response code for refund and void operations

        SRV_ADDRESS = (config_dict['addr'], int(config_dict['port']))
        PROCESS_TIME = int(config_dict['tptp_stat_time'])
        OWN_PROCESS_TIME = int(config_dict['own_stat_time'])
        PRINT_HEX = bool(int(config_dict['hexd']))
        PROTOCOL = str(config_dict['protocol']).upper()
        PARSE = bool(int(config_dict['parse']))
        INPUT_DATA = list()
        OUTPUT_DATA = list()
        LAST_REQUEST = dict()
        TIMER_CONN_LIST = list()
        STATUS_TIMER_LIST = list()

        VOID_DELAY = int(config_dict['void_time'])
        FINAL_DELAY = int(config_dict['final_time'])
        STATUS_DELAY = int(config_dict['status_time'])
        REFUND_DELAY = int(config_dict['refund_time'])
        QR_CODE_DELAY = int(config_dict['qr_code_time'])
        DEFAULT_DELAY = int(config_dict['default_time'])
        CLOSE_OP_DELAY = int(config_dict['close_op_time'])

        RC_DICT = {'cl_batch': bool(int(config_dict['tptp_cl_batch'])),
                   'sale_rc': bool(int(config_dict['stat'])),
                   'refund_rc': REFUND_RC,
                   'void_rc': VOID_RC}

        OWN_RC_DICT = {'cl_batch': bool(int(config_dict['own_cl_batch'])),
                       'sale_rc': OWN_SALE_RC,
                       'refund_rc': OWN_REFUND_RC}

        if PROTOCOL != 'OWN' and PROTOCOL != 'TPTP':
            print('Wrong PROTOCOL value!')
            input('Press ENTER to exit.')
            sys.exit()
    except ValueError:
        print('Wrong values in config.ini!')
        input('Press ENTER to exit.')
        sys.exit()


def get_server_socket():
    server = socket()
    server.setblocking(False)
    server.bind(SRV_ADDRESS)
    server.listen(10)
    return server


def ready_to_answer(addr, resp=None):
    for conn in TIMER_CONN_LIST:
        if addr in conn:
            if time.perf_counter() > conn[1]:
                TIMER_CONN_LIST.pop(TIMER_CONN_LIST.index(conn))
                return True
            else:
                return False
    else:
        cur_time = time.perf_counter()
        if len(resp) >= 49:
            try:
                if resp[41:43] == b'00' or resp[2:4] == b'\x94\x30':
                    TIMER_CONN_LIST.append([addr, cur_time + VOID_DELAY])
                elif resp[41:43] == b'01' or resp[2:4] == b'\x97\x10':
                    TIMER_CONN_LIST.append([addr, cur_time + QR_CODE_DELAY])
                elif resp[41:43] == b'02' or resp[2:4] == b'\x02\x30':
                    TIMER_CONN_LIST.append([addr, cur_time + FINAL_DELAY])
                elif resp[41:43] == b'04' or resp[2:4] == b'\x02\x10':
                    TIMER_CONN_LIST.append([addr, cur_time + REFUND_DELAY])
                elif resp[41:43] == b'36' or resp[2:4] == b'\x06\x30':
                    TIMER_CONN_LIST.append([addr, cur_time + STATUS_DELAY])
                else:
                    TIMER_CONN_LIST.append([addr, cur_time + DEFAULT_DELAY])

                for connect in TIMER_CONN_LIST:
                    if addr in connect:
                        if TIMER_CONN_LIST[TIMER_CONN_LIST.index(connect)][1] == cur_time:
                            return True
                        else:
                            return False

            except TypeError as e:
                resp_gen.set_logging(); logging.error(f'ERROR:\n{e}')
                return False
        else:
            if resp:
                TIMER_CONN_LIST.append([addr, cur_time + CLOSE_OP_DELAY])
            return False


def status_ready(peer_name, request):
    if PROTOCOL == 'TPTP':
        if request[41:43] == '36':
            if PROCESS_TIME == 0:
                return True
            else:
                cur_time = time.perf_counter()
                for peer in STATUS_TIMER_LIST:
                    if peer_name in peer:
                        if cur_time > peer[1]:
                            return True
                        else:
                            return False
                else:
                    STATUS_TIMER_LIST.append([peer_name, cur_time + PROCESS_TIME])
                    return False
        else:
            return True
    elif PROTOCOL == 'OWN':
        if request[2:4] == b'\x06\x20':
            if OWN_PROCESS_TIME == 0:
                return True
            else:
                cur_time = time.perf_counter()
                for peer in STATUS_TIMER_LIST:
                    if peer_name in peer:
                        if cur_time > peer[1]:
                            return True
                        else:
                            return False
                else:
                    STATUS_TIMER_LIST.append([peer_name, cur_time + OWN_PROCESS_TIME])
                    return False


def handle_writables(writs):
    for resource in writs:
        try:
            if PROTOCOL == 'TPTP':
                req = LAST_REQUEST[resource.getpeername()].decode('utf-8')
                resp = resp_gen.form_answer(req,
                                            RC_DICT,
                                            status_ready(resource.getpeername(), req))
            elif PROTOCOL == 'OWN':
                req = LAST_REQUEST[resource.getpeername()]
                resp = open_way.form_answer(req,
                                            OWN_RC_DICT,
                                            status_ready(resource.getpeername(), req))
            else:
                resp = None

            if resp and ready_to_answer(resource.getpeername(), resp):
                if PROTOCOL == 'TPTP':
                    print(f'RESPONSE TO {resource.getpeername()}:\n{resp_gen.print_req_res(resp)}\n')
                    resp_gen.set_logging()
                    logging.info(f'RESPONSE TO  {resource.getpeername()}:{str(resp)}')

                    if PRINT_HEX: print(resp_gen.print_hex_dump(resp))
                    if PARSE:
                        values = resp_gen.parse_data(resp)
                        if values:
                            for val in values:
                                print('{:20}:{}'.format(val, values[val]))
                            print('\n', end='')
                    resource.send(resp)
                    OUTPUT_DATA.remove(resource)

                    if resp.decode('utf-8').find('SUCCESS') != -1 or resp.decode('utf-8').find('FAILED') != -1:
                        for peer in STATUS_TIMER_LIST:
                            if resource.getpeername() in peer:
                                STATUS_TIMER_LIST.pop(STATUS_TIMER_LIST.index(peer))
                elif PROTOCOL == 'OWN':
                    print(f'RESPONSE TO {resource.getpeername()}:\n{resp}\n')
                    resp_gen.set_logging()
                    logging.info(f'RESPONSE TO  {resource.getpeername()}:{str(resp)}')

                    if PRINT_HEX: print(resp_gen.print_hex_dump(resp[2:]))
                    if PARSE:
                        values = open_way.get_values(resp)
                        if values:
                            for val in values:
                                print('{:2}:{}'.format(val, values[val]))
                            print('\n', end='')
                    resource.send(resp)
                    OUTPUT_DATA.remove(resource)

                    if resp[2:4] == b'\x06\x30' and resp[43:45] != b'09':
                        for peer in STATUS_TIMER_LIST:
                            if resource.getpeername() in peer:
                                STATUS_TIMER_LIST.pop(STATUS_TIMER_LIST.index(peer))
        except OSError:
            clear_resource(resource)


def handle_readables(reads, server):
    for resource in reads:
        if resource is server:
            conn, addr = resource.accept()
            conn.setblocking(False)
            INPUT_DATA.append(conn)
            print(f'New connection:{addr}\n')
            resp_gen.set_logging(); logging.info(f'New connection:{str(conn)}')
            if PROTOCOL == 'TPTP':
                conn.send(b'\x05')
        else:
            data = b''
            try:
                data = resource.recv(1024)
            except ConnectionResetError:
                pass

            if data:
                if PROTOCOL == 'TPTP':
                    print(f'REQUEST FROM {resource.getpeername()}:\n{resp_gen.print_req_res(data)}\n')
                elif PROTOCOL == 'OWN':
                    print(f'REQUEST FROM {resource.getpeername()}:\n{data}\n')

                resp_gen.set_logging()
                logging.info(f'REQUEST FROM {resource.getpeername()}:{str(data)}')

                if PRINT_HEX:
                    if PROTOCOL == 'TPTP':
                        print(resp_gen.print_hex_dump(data))
                    elif PROTOCOL == 'OWN':
                        print(resp_gen.print_hex_dump(data[2:]))
                if PARSE:
                    if PROTOCOL == 'OWN':
                        values = open_way.get_values(data)
                        if values:
                            for val in values:
                                print('{:2}:{}'.format(val, values[val]))
                            print('\n', end='')
                    elif PROTOCOL == 'TPTP':
                        values = resp_gen.parse_data(data)
                        if values:
                            for val in values:
                                print('{:20}:{}'.format(val, values[val]))
                            print('\n', end='')
                if resource.getpeername() not in LAST_REQUEST:
                    LAST_REQUEST.update({resource.getpeername(): data})
                else:
                    LAST_REQUEST[resource.getpeername()] = data

                if resource not in OUTPUT_DATA:
                    OUTPUT_DATA.append(resource)
            else:
                clear_resource(resource)


def clear_resource(res):
    try:
        if res in INPUT_DATA:
            INPUT_DATA.remove(res)
        if res in OUTPUT_DATA:
            OUTPUT_DATA.remove(res)
        print(f'Connection closed:{str(res.getpeername())}\n')
        resp_gen.set_logging(); logging.info(f'Connection closed:{str(res)}')
        res.close()
    except Exception as e:
        resp_gen.set_logging()
        logging.info(f'ERROR:\n{e}')


if __name__ == '__main__':
    setup_vars()  # initiates variables
    time.perf_counter()  # initiates timer
    resp_gen.check_log_files()  # controls maximal log files

    try:
        srv_socket = get_server_socket()
    except OSError:
        print('Program is already running or address/port is wrong!')
        input('Press ENTER to exit.')
        sys.exit()

    INPUT_DATA.append(srv_socket); print(f'----------Alipay test server v{version.get_version()}----------')
    resp_gen.set_logging(); logging.info(f'Server started {srv_socket}')

    try:
        while INPUT_DATA:
            readables, writables, exceptional = select(INPUT_DATA, OUTPUT_DATA, INPUT_DATA)
            handle_readables(readables, srv_socket)
            handle_writables(writables)
    except KeyboardInterrupt:
        clear_resource(srv_socket)
        print('Server stopped!')
        resp_gen.set_logging(); logging.info('Server stopped!')
