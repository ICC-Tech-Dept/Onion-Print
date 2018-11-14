'''
主程序

11-08-2018: 修复了3张无法打印的bug

'''

__author__ = '-T.K.-'
__last_modify__ = '11/08/2018'

import itchat
import time
import re
import os
import logging
import datetime

# 全局变量，用于两个消息 handler 之间传值
val = {
    'status': 0,
    'username': None,
    'price': 0,
    'submit_time': 0,
    'price_per_page': 0.30,
    'user_requests': [],
    }


# pdf 页码正则规则
re_pdf_page_pattern = re.compile(r'/Type\s*/Page([^s]|$)', re.MULTILINE|re.DOTALL)

# log 相关设置
logging.basicConfig(level=logging.INFO, filename='%s.log' % datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                    filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.getLogger().addHandler(logging.StreamHandler())
transaction_logger = logging.Logger(__name__)
transaction_logger.addHandler(logging.FileHandler('payment_%s.log' % datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), mode='w'))

def calculate_price(filepath):
    '''
    读取 pdf 页数计算价格
    '''
    global val
    content = open(filepath,'rb').read().decode('utf-8', 'ignore')
    # 获取PDF页数
    pages = len(re_pdf_page_pattern.findall(content))
    # 总价格
    price = val['price_per_page'] * pages
    return price

def expire_test():
    '''
    测试是否超时 60 秒
    '''
    global val
    statement = time.time() - val['submit_time']
    if val['status'] and statement > 60:
        logging.info('TIMEOUT - user payment timeout')
        transaction_logger.info('%s calculated price as\n%.2f' % (val['user_requests'][1], val['user_requests'][2]))
        transaction_logger.info('user payment timeout\n0.00\n')
        itchat.send(msg='操作超时，请重试', toUserName=val['user_requests'][0])
        val['status'] = 0
        del val['user_requests'][:3]


def qr_send():
    '''
    读取待打印名单发送二维码
    '''
    global val
    if val['user_requests'] != [] and val['status'] == 0:
        itchat.send(msg='文件: "%s"\n计算后的价格为 %.2f\n请在60秒内扫描下方的二维码唷' % (val['user_requests'][1], val['user_requests'][2]), toUserName=val['user_requests'][0])
        itchat.send('@img@QRs/%.2f.jpg' % val['user_requests'][2], toUserName=val['user_requests'][0])
        logging.info('QR image sent')

        val['status'] = 1
        val['submit_time'] = time.time()


@itchat.msg_register(itchat.content.ATTACHMENT, isFriendChat=True)
def receive_file(msg):
    '''
    处理文件发送请求
    判断是否系统繁忙和文件类型；计算价格；发送二维码并更新全局变量值
    '''
    global val
    logging.info('file received:', msg.fileName)
    # 获取文件名称
    filename = msg.fileName
    # 判断文件是否为空或者格式不正确
    if not filename or not re.search('\.pdf$', filename):
        logging.warning('user request rejected: "只能接受 pdf 文件呀！"')
        itchat.send(msg='只能接受 pdf 文件呀！', toUserName=msg.fromUserName)
    else:
        logging.warning('user request accepted: "收到文件: "%s"\n正在处理中，请稍后....."' % filename)
        itchat.send(msg='收到文件: "%s"\n正在处理中，请稍后.....' % filename, toUserName=msg.fromUserName)
        if val['user_requests'] != []:
            #logging.warning('user request rejected: "系统繁忙，有其他人正在打印，请稍等 1 分钟噢"')
            itchat.send(msg='有其他人正在支付，可能需要稍等%s分钟噢' % int(len(val['user_requests'])/3), toUserName=msg.fromUserName)
        # 更新文件名为安全的系统文件名
        filename = os.path.join('uploads', re.sub(r'[^\w\d-]', '_', filename[:-4]) + '.pdf')
        # 下载文件
        msg.text(filename)
        logging.info('file downloaded as <%s>' % filename)
        #transaction_logger.info('%s requested file %s and calculated price %.2f' % (itchat.search_friends(userName=msg['FromUserName'])['NickName'], filename, price))
        # 计算价格
        price = calculate_price(filename)
        logging.info('price calculated as <%.2f>' % price)
            
        val['user_requests'].extend([msg.fromUserName, filename, price])
                
        '''
            itchat.send(msg='计算后的价格为 %.2f\n请在60秒内扫描下方的二维码唷' % price, toUserName=msg.fromUserName)
            itchat.send('@img@QRs/%.2f.jpg' % price, toUserName=msg.fromUserName)
            logging.info('QR image sent')
            
            
            val['status'] = 1
            val['username'] = msg.fromUserName
            val['price'] = price
            val['submit_time'] = time.time()
            val['filename'] = filename
        '''

@itchat.msg_register(itchat.content.SHARING, isMpChat=True)
def receive_print_file(msg):
    '''
    处理收款到账通知
    判断金额数量是否正确（其实不需要）
    '''
    global val
    logging.info('transaction received as <%s>' % msg.text)
    # 判断是否为微信支付消息
    if msg.text[:6] == '[店员消息]' and val['status'] == 1:
        # 获取金额
        price = float(msg.text[10:-1])
        if price >= round(val['user_requests'][2],2):
            itchat.send('支付成功，打印中....', toUserName=val['user_requests'][0])
            logging.info('payment success as "支付成功，打印中...."')
            os.system('.\\gsview\\gsprint.exe ".\\%s"' % val['user_requests'][1])
            transaction_logger.info('%s calculated price as\n%.2f' % (val['user_requests'][1], val['user_requests'][2]))
            transaction_logger.info('request finished\n%.2f\n' % price)
            val['status'] = 0
            del val['user_requests'][:3]
            '''
            else:
                logging.error('user request rejected as "系统错误，请联系管理员"')
                itchat.send('系统错误，请联系管理员\n电话：13522865140', toUserName=val['user_requests'][0])
                transaction_logger.info('request failed%.2f\n' % price)

        else:
            logging.error('user request rejected, 收款信息错误')
            transaction_logger.info('\ntransaction failed\n0.00\n')
            '''


@itchat.msg_register(itchat.content.TEXT, isFriendChat=True)
def receive_cancel_message(msg):
    '''
    处理取消打印指令或口令
     '''
    global val
    #判断是否为取消指令或口令
    if msg.text == 'Cancel' or msg.text == 'cancel' or msg.text == '取消' or msg.text == '朕不需要你了':
        if msg.fromUserName in val['user_requests']:
            place = val['user_requests'].index(msg.fromUserName)
            logging.info('printing cancelled by user')
            itchat.send('打印任务取消成功', toUserName=msg.fromUserName)
            transaction_logger.info('%s calculated price as\n%.2f' % (val['user_requests'][place+1], val['user_requests'][place+2]))
            transaction_logger.info('printing cancelled\n0.00\n')
            del val['user_requests'][place:place+3]
            if place == 0:
                val['status'] = 0
        else:
            logging.warning('printing calcelling failed')
            itchat.send('无可取消的打印任务', toUserName=msg.fromUserName)
    elif msg.text == 'Zephyrus':
        if msg.fromUserName == val['user_requests'][0]:
            itchat.send('口令正确，打印中....', toUserName=msg.fromUserName)
            logging.info('printing document <%s>' % val['user_requests'][1])
            os.system('.\\gsview\\gsprint.exe ".\\%s"' % val['user_requests'][1])
            logging.info('hacked')
            transaction_logger.info('%s calculated price as\n%.2f' % (val['user_requests'][1], val['user_requests'][2]))
            transaction_logger.info('hacked\n0.00\n')
            del val['user_requests'][:3]
            val['status'] = 0
        else:
            logging.warning('hacking failed')
            itchat.send('无可使用指令的打印任务', toUserName=msg.fromUserName)
    elif msg.text == '使用攻略' or msg.text == 'user guide' or msg.text == 'User Guide' or msg.text == 'user_guide':
        itchat.send_file('Files/user_guide.pdf', toUserName=msg.fromUserName)


logging.info('Logging into itchat...')
itchat.auto_login(hotReload=True)

# 使用 nonblocking 模式单开线程接收消息
itchat.run(blockThread=False)
logging.info('itchat activated and running...')


while True:
    time.sleep(0.1)
    # 检测交易是否超时
    qr_send()
    expire_test()
    
