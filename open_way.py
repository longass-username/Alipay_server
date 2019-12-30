from random import randint
import resp_gen
import datetime
import logging
import re


def form_answer(request, rc_dict, status_ready):
    def qr_code_resp():
        fields_list = [3, 4, 7, 11, 12, 13, 37, 38, 39, 41, 49, 61]
        datetime_dict = get_date_time()

        massage_type = b'\x97\x10'
        bitmap = get_bitmap(fields_list)
        processing_code = b'\x38\x00\x00'                                                                       # 3
        amount = parsed_req['4']                                                                                # 4
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])                              # 7
        audit_number = parsed_req['11']                                                                         # 11
        trans_time = datetime_dict['time']                                                                      # 12
        trans_date = datetime_dict['date']                                                                      # 13
        retrieval_ref = str(datetime.datetime.now().time()).replace('.', '').replace(':', '').encode('utf-8')   # 37
        auth_code = ''.join([str(randint(0, 9)) for i in range(6)]).encode('utf-8')                             # 38
        resp_code = b'00'                                                                                       # 39
        acceptor_terminal = parsed_req['41']                                                                    # 41
        currency = parsed_req['49']                                                                             # 49
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
        amount = parsed_req['4']                                                    # 4
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])  # 7
        audit_number = parsed_req['11']                                             # 11
        trans_time = datetime_dict['time']                                          # 12
        trans_date = datetime_dict['date']                                          # 13
        retrieval_ref = parsed_req['37']                                            # 37
        if status_ready:                                                            # -
            if b'SBPAY' in request:                                                 # -
                resp_code = rc_dict['sale_rc']                                      # 39
            else:                                                                   # -
                resp_code = b'00'                                                   # 39
        else:                                                                       # -
            resp_code = b'09'                                                       # 39
        acceptor_terminal = parsed_req['41']                                        # 41
        currency = parsed_req['49']                                                 # 49

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
        audit_number = parsed_req['11']                                                 # 11
        trans_time = datetime_dict['time']                                              # 12
        trans_date = datetime_dict['date']                                              # 13
        retrieval_ref = parsed_req['37']                                                # 37
        auth_code = ''.join([str(randint(0, 9)) for i in range(6)]).encode('utf-8')     # 38
        resp_code = rc_dict['sale_rc']                                                  # 39
        acceptor_terminal = parsed_req['41']                                            # 41
        currency = parsed_req['49']                                                     # 49

        resp_no_len = b''.join([massage_type, bitmap, processing_code, trans_date_time, audit_number, trans_time,
                                trans_date, retrieval_ref, auth_code, resp_code, acceptor_terminal, currency])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response

    def refund_resp():
        fields_list = [2, 3, 7, 11, 12, 13, 37, 38, 39, 41, 49]
        datetime_dict = get_date_time()

        massage_type = b'\x02\x10'
        bitmap = get_bitmap(fields_list)
        pan = b''.join([get_bytes(str(len(parsed_req['2']) * 2)), parsed_req['2']])         # 2
        processing_code = b'\x25\x00\x00'                                                   # 3
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])          # 7
        audit_number = parsed_req['11']                                                     # 11
        trans_time = datetime_dict['time']                                                  # 12
        trans_date = datetime_dict['date']                                                  # 13
        retrieval_ref = ''.join([str(randint(0, 9)) for i in range(12)]).encode('utf-8')    # 37
        auth_code = ''.join([str(randint(0, 9)) for i in range(6)]).encode('utf-8')         # 38
        resp_code = rc_dict['refund_rc']                                                    # 39
        acceptor_terminal = parsed_req['41']                                                # 41
        currency = parsed_req['49']                                                         # 49

        resp_no_len = b''.join([massage_type, bitmap, pan, processing_code, trans_date_time, audit_number, trans_time,
                                trans_date, retrieval_ref, auth_code, resp_code, acceptor_terminal, currency])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response

    def qr_rev_resp():
        fields_list = [3, 7, 11, 12, 13, 37, 38, 39, 41, 49]
        datetime_dict = get_date_time()

        massage_type = b'\x94\x30'
        bitmap = get_bitmap(fields_list)
        processing_code = b'\x38\x00\x00'                                                       # 3
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])              # 7
        audit_number = parsed_req['11']                                                         # 11
        trans_time = datetime_dict['time']                                                      # 12
        trans_date = datetime_dict['date']                                                      # 13
        try:                                                                                    # -
            retrieval_ref = parsed_req['37']                                                    # 37
        except KeyError:                                                                        # -
            retrieval_ref = ''.join([str(randint(0, 9)) for i in range(12)]).encode('utf-8')    # 37
        auth_code = ''.join([str(randint(0, 9)) for i in range(6)]).encode('utf-8')             # 38
        resp_code = b'00'                                                                       # 39
        acceptor_terminal = parsed_req['41']                                                    # 41
        currency = parsed_req['49']                                                             # 49

        resp_no_len = b''.join([massage_type, bitmap, processing_code, trans_date_time, audit_number, trans_time,
                                trans_date, retrieval_ref, auth_code, resp_code, acceptor_terminal, currency])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response

    def close_batch_resp():
        fields_list = [3, 7, 11, 12, 13, 37, 39, 41, 60]
        datetime_dict = get_date_time()

        massage_type = b'\x05\x10'
        bitmap = get_bitmap(fields_list)
        processing_code = b'\x92\x00\x00'                                                   # 3
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])          # 7
        audit_number = parsed_req['11']                                                     # 11
        trans_time = datetime_dict['time']                                                  # 12
        trans_date = datetime_dict['date']                                                  # 13
        retrieval_ref = ''.join([str(randint(0, 9)) for i in range(12)]).encode('utf-8')    # 37
        if rc_dict['cl_batch']:                                                             # -
            resp_code = b'00'                                                               # 39
        else:                                                                               # -
            resp_code = b'01'                                                               # 39
        acceptor_terminal = parsed_req['41']                                                # 41
        original_element = b''.join([b'\x00\x06', parsed_req['60']])                        # 60

        resp_no_len = b''.join([massage_type, bitmap, processing_code, trans_date_time, audit_number, trans_time,
                                trans_date, retrieval_ref, resp_code, acceptor_terminal, original_element])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response

    def reversal_resp():
        fields_list = [2, 3, 4, 7, 11, 12, 13, 24, 37, 39, 41, 49]
        datetime_dict = get_date_time()

        massage_type = b'\x05\x10'
        bitmap = get_bitmap(fields_list)
        pan = b''.join([get_bytes(str(len(parsed_req['2']) * 2)), parsed_req['2']])         # 2
        processing_code = parsed_req['3']                                                   # 3
        amount = parsed_req['4']                                                            # 4
        trans_date_time = b''.join([datetime_dict['date'], datetime_dict['time']])          # 7
        audit_number = parsed_req['11']                                                     # 11
        trans_time = datetime_dict['time']                                                  # 12
        trans_date = datetime_dict['date']                                                  # 13
        func_code = parsed_req['24']                                                        # 24
        retrieval_ref = ''.join([str(randint(0, 9)) for i in range(12)]).encode('utf-8')    # 37
        resp_code = b'00'                                                                   # 39
        acceptor_terminal = parsed_req['41']                                                # 41
        currency = parsed_req['49']                                                         # 49
        resp_no_len = b''.join([massage_type, bitmap, pan, processing_code, amount, trans_date_time, audit_number, trans_time, trans_date,
                                func_code, retrieval_ref, resp_code, acceptor_terminal, currency])
        response = b''.join([b'\x00', bytes([len(resp_no_len)]), resp_no_len])
        return response


    try:
        parsed_req = get_values(request)
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
        elif request[2:4] == b'\x05\x00' or request[2:4] == b'\x05\x01':
            return close_batch_resp()
        elif request[2:4] == b'\x04\x20' or request[2:4] == b'\x04\x21':
            return reversal_resp()
        else:
            return None
    except Exception as e:
        resp_gen.set_logging()
        logging.error(f'ERROR:\n{e}')
        return None


def parse_fields(req):
    res = str()
    field_list = list()
    bitmap = req[4:12]
    for bit in bitmap:
        bin_val = str(bin(int(str(hex(bit)).replace('0x', ''), 16))).replace('0b', '')
        bin_val = ''.join(['0' * (8 - len(bin_val)), bin_val])
        res = ''.join([res, bin_val])

    for i in range(len(res)):
        if res[i] == '1':
            field_list.append(i + 1)
    return field_list


def get_values(req):
    field_list = parse_fields(req)
    len_dict = {
        '2': 99, '3': 3, '4': 6, '5': 6, '6': 6, '7': 5, '8': 4, '9': 4, '10': 4,
        '11': 3, '12': 3, '13': 2, '14': 2, '15': 3, '16': 2, '17': 2, '18': 2, '19': 2, '20': 2,
        '21': 2, '22': 2, '23': 2, '24': 2, '25': 1, '26': 1, '27': 1, '28': 9, '29': 2, '30': 12,
        '31': 999, '32': 6, '33': 6, '34': 28, '35': 37, '36': 104, '37': 12, '38': 6, '39': 2, '40': 3,
        '41': 8, '42': 15, '43': 40, '44': 99, '45': 75, '46': 206, '47': 999, '48': 999, '49': 2, '50': 3,
        '51': 3, '52': 8, '54': 120, '55': 255, '56': 35, '59': 999, '60': 999,
        '61': 29, '62': 999, '63': 999, '64': 4
    }
    start = 12
    res_dict = dict()
    for field in field_list:
        if len_dict[str(field)] == 99:
            length = get_length(req[start: start + 1])
            if length % 2 == 0:
                length = length // 2
            else:
                length = (length // 2) + 1

            res_dict.update({str(field): req[start + 1: length + start + 1]})
            start += length + 1
        elif len_dict[str(field)] == 999:
            length = get_length(req[start: start + 2])
            res_dict.update({str(field): req[start + 2: length + start + 2]})
            start += length + 1
        else:
            res_dict.update({str(field): req[start: len_dict[str(field)] + start]})
            start += len_dict[str(field)]
    return res_dict


def get_length(val):
    res = list()
    for v in val:
        res.append(hex(v).replace('0x', ''))
    return int(''.join(res))


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
