from binascii import unhexlify
from socket import socket
from select import select
import resp_gen
import version
import logging
import sys


def setup_vars():
    global SRV_ADDRESS
    global INPUT_DATA
    global OUTPUT_DATA
    global PRINT_HEX
    global LAST_REQUEST

    try:
        config_dict = resp_gen.conf_parser()
        SRV_ADDRESS = (config_dict['addr'], int(config_dict['port']))
        PRINT_HEX = bool(int(config_dict['hexd']))
        INPUT_DATA = list()
        OUTPUT_DATA = list()
        LAST_REQUEST = dict()
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


def handle_writables(writs):
    for resource in writs:
        try:
            resp = resp_gen.form_answer(LAST_REQUEST[resource.getpeername()].decode('utf-8'))
            print(f'RESPONSE TO {resource.getpeername()}:\n{resp_gen.print_req_res(resp)}\n')
            resp_gen.set_logging()
            logging.info(f'RESPONSE TO  {resource.getpeername()}:{str(resp)}')

            if PRINT_HEX:
                print(resp_gen.print_hex_dump(resp))
            if resp:
                resource.send(resp)
            OUTPUT_DATA.remove(resource)
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
            conn.send(b'\x05')
        else:
            data = b''
            try:
                data = resource.recv(1024)
            except ConnectionResetError:
                pass

            if data:
                print(f'REQUEST FROM {resource.getpeername()}:\n{resp_gen.print_req_res(data)}\n')
                resp_gen.set_logging()
                logging.info(f'REQUEST FROM {resource.getpeername()}:{str(data)}')

                if PRINT_HEX:
                    print(resp_gen.print_hex_dump(data))

                if resource.getpeername() not in LAST_REQUEST:
                    LAST_REQUEST.update({resource.getpeername(): data})
                else:
                    LAST_REQUEST[resource.getpeername()] = data

                if resource not in OUTPUT_DATA:
                    OUTPUT_DATA.append(resource)
            else:
                clear_resource(resource)


def clear_resource(res):
    if res in INPUT_DATA:
        INPUT_DATA.remove(res)
    if res in OUTPUT_DATA:
        OUTPUT_DATA.remove(res)
    print(f'Connection closed:{str(res.getpeername())}\n')
    resp_gen.set_logging(); logging.info(f'Connection closed:{str(res)}')
    res.close()


if __name__ == '__main__':
    setup_vars()
    resp_gen.check_log_files()

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
