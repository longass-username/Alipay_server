from random import randint
import datetime
import re


def form_answer(request, rc_dict, main_dict, status_ready):
    def qr_code_resp():
        fields_list = [3, 4, 7, 11, 12, 13, 37, 38, 39, 41, 49, 61]
        datetime_dict = get_date_time()

        massage_type = b'\x97\x10'
        bitmap = get_bitmap(fields_list)
        processing_code = b'\x38\x00\x00'                                                                       # 3
        amount = request[15:21]                                                                                 # 4
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])                              # 7
        audit_number = request[26:29]                                                                           # 11
        trans_time = datetime_dict['time']                                                                      # 12
        trans_date = datetime_dict['date']                                                                      # 13
        retrieval_ref = str(datetime.datetime.now().time()).replace('.', '').replace(':', '').encode('utf-8')   # 37
        auth_code = ''.join([str(randint(0, 9)) for i in range(6)]).encode('utf-8')                             # 38
        resp_code = b'00'                                                                                       # 39
        acceptor_terminal = main_dict['terminal'].encode('utf-8')                                               # 41
        currency = get_bytes(main_dict['currency'])                                                             # 49
        qr_code = b'\x00\x00\x26\xeb\x18\xf2\x16\xc2\x14\x54https://example.com'                                # 61

        resp_no_len = b''.join([massage_type, bitmap, processing_code, amount, trans_date_time, audit_number,
                                trans_time, trans_date, retrieval_ref, auth_code, resp_code, acceptor_terminal,
                                currency, qr_code])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response

    def status_resp():
        fields_list = [4, 7, 11, 12, 13, 37, 39, 41, 49]
        datetime_dict = get_date_time()

        massage_type = b'\x06\x30'
        bitmap = get_bitmap(fields_list)
        amount = request[12:18]                                                     # 4
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])  # 7
        audit_number = request[23:26]                                               # 11
        trans_time = datetime_dict['time']                                          # 12
        trans_date = datetime_dict['date']                                          # 13
        retrieval_ref = request[28:40]                                              # 37
        if status_ready:                                                            # -
            resp_code = b'00'                                                       # 39
        else:                                                                       # -
            resp_code = b'09'                                                       # 39
        acceptor_terminal = main_dict['terminal'].encode('utf-8')                   # 41
        currency = get_bytes(main_dict['currency'])                                 # 49

        resp_no_len = b''.join([massage_type, bitmap, amount, trans_date_time, audit_number, trans_time, trans_date,
                                retrieval_ref, resp_code, acceptor_terminal, currency])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response

    def final_sale_resp():
        fields_list = [3, 7, 11, 12, 13, 37, 38, 39, 41, 49]
        datetime_dict = get_date_time()

        massage_type = b'\x02\x30'
        bitmap = get_bitmap(fields_list)
        processing_code = b'\x00\x00\x00'                                               # 3
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])      # 7
        audit_number = request[26:29]                                                   # 11
        trans_time = datetime_dict['time']                                              # 12
        trans_date = datetime_dict['date']                                              # 13
        retrieval_ref = request[31:43]                                                  # 37
        auth_code = ''.join([str(randint(0, 9)) for i in range(6)]).encode('utf-8')     # 38
        resp_code = rc_dict['sale_rc']                                                  # 39
        acceptor_terminal = main_dict['terminal'].encode('utf-8')                       # 41
        currency = get_bytes(main_dict['currency'])                                     # 49

        resp_no_len = b''.join([massage_type, bitmap, processing_code, trans_date_time, audit_number, trans_time,
                                trans_date, retrieval_ref, auth_code, resp_code, acceptor_terminal, currency])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response

    def refund_resp():
        fields_list = [2, 3, 7, 11, 12, 13, 37, 38, 39, 41, 49]
        datetime_dict = get_date_time()

        massage_type = b'\x02\x10'
        bitmap = get_bitmap(fields_list)
        pan = request[12:21]                                                                # 2
        processing_code = b'\x25\x00\x00'                                                   # 3
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])          # 7
        audit_number = request[35:38]                                                       # 11
        trans_time = datetime_dict['time']                                                  # 12
        trans_date = datetime_dict['date']                                                  # 13
        retrieval_ref = ''.join([str(randint(0, 9)) for i in range(12)]).encode('utf-8')    # 37
        auth_code = ''.join([str(randint(0, 9)) for i in range(6)]).encode('utf-8')         # 38
        resp_code = rc_dict['refund_rc']                                                    # 39
        acceptor_terminal = main_dict['terminal'].encode('utf-8')                           # 41
        currency = get_bytes(main_dict['currency'])                                         # 49

        resp_no_len = b''.join([massage_type, bitmap, pan, processing_code, trans_date_time, audit_number, trans_time,
                                trans_date, retrieval_ref, auth_code, resp_code, acceptor_terminal, currency])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response

    def qr_rev_resp():
        fields_list = [3, 7, 11, 12, 13, 37, 38, 39, 41, 49]
        datetime_dict = get_date_time()

        massage_type = b'\x94\x30'
        bitmap = get_bitmap(fields_list)
        processing_code = b'\x38\x00\x00'                                               # 3
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])      # 7
        audit_number = request[26:29]                                                   # 11
        trans_time = datetime_dict['time']                                              # 12
        trans_date = datetime_dict['date']                                              # 13
        retrieval_ref = request[31:43]                                                  # 37
        auth_code = ''.join([str(randint(0, 9)) for i in range(6)]).encode('utf-8')     # 38
        resp_code = b'00'                                                               # 39
        acceptor_terminal = main_dict['terminal'].encode('utf-8')                       # 41
        currency = get_bytes(main_dict['currency'])                                     # 49

        resp_no_len = b''.join([massage_type, bitmap, processing_code, trans_date_time, audit_number, trans_time,
                                trans_date, retrieval_ref, auth_code, resp_code, acceptor_terminal, currency])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response

    if request[2:4] == b'\x97\x00':
        return qr_code_resp()
    elif request[2:4] == b'\x06\x20':
        return status_resp()
    elif request[2:4] == b'\x02\x20':
        return final_sale_resp()
    elif request[2:4] == b'\x02\x00':
        return refund_resp()
    elif request[2:4] == b'\x94\x20':
        return qr_rev_resp()
    else:
        return None


def get_date_time():
    time_res = list()
    date_res = list()

    now = datetime.datetime.now()
    time = str(now).split(' ')[1].split('.')[0].split(':')
    date = str(now).split(' ')[0].split('-')[1:]
    for t in time:
        time_res.append(int(t, 16))
    for d in date:
        date_res.append(int(d, 16))
    return {'date': bytes(date_res),
            'time': bytes(time_res)}


def get_bitmap(field_list):
    bitmap = [0 for i in range(64)]
    for field_num in field_list:
        bitmap[field_num - 1] = 1

    res = list()
    for i in range(8):
        binary = str()
        for j in range(8):
            binary += str(bitmap.pop(0))
        hexademical = hex(int(binary, 2)).replace('0x', '')
        if len(hexademical) == 2:
            res.append(hexademical)
        else:
            res.append('0' + hexademical)
    for num in res:
        res[res.index(num)] = int(str(num), 16)
    return bytes(res)


def get_bytes(text):
    res = list()
    if len(text) % 2 != 0:
        text = ''.join(['0', text])
    for i in range(len(text) // 2):
        res.append(int(text[i*2:i*2+2], 16))
    return bytes(res)
