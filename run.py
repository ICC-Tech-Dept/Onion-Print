import itchat

def send_QR_payment(amount):
    '''
    send the QR image of corresponding money.
    @param amount: the amount of money needed, type float.
    '''
    pass

def start_timer():
    '''
    start the 100s timer
    '''
    pass


def listen_message():
    '''
    listen to the itchat ATTACHMENT message,
    download the file in the '/uploads/' folder,
    and start the following operation
    '''
    pass
    download_file()
    send_QR_payment()
    start_timer()
    reply = wait_for_reply()
    if reply:
        reply_message('success')
    else:
        reply_message('failed')


def run():
    ''' run the program '''
    pass
