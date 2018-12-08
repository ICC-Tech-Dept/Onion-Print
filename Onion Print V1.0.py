'''
主程序

修复bug  优化双面打印  取消除交钱报告的一切transaction logger

正式版V1.0

'''

__author__ = '-T.K.-'
__modefier__= 'DessertFox-M'
__last_modify__ = '12/08/2018'

import itchat
import time
import re
import os
import logging
import datetime
from PyPDF2 import PdfFileReader, PdfFileWriter

# 全局变量，用于两个消息 handler 之间传值
val = {
    'status': 0,
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


def expire_test():
    '''
    测试是否超时 60 秒
    '''
    global val
    statement = time.time() - val['submit_time']
    if (val['status'] == 1 or val['status'] == 2) and statement > 60:
        logging.info('TIMEOUT - user payment timeout')
        itchat.send(msg='操作超时，请重试', toUserName=val['user_requests'][0][0])
        val['status'] = 0
        del val['user_requests'][0]


def qr_send():
    '''
    读取待打印名单发送二维码
    '''
    global val
    if val['user_requests'] != [] and val['status'] == 0 and val['user_requests'][0][2] != 0:
        itchat.send(msg='文件: "%s"\n计算后的价格为 %.2f\n请在60秒内扫描下方的二维码唷' % (val['user_requests'][0][1], val['user_requests'][0][2]), toUserName=val['user_requests'][0][0])
        itchat.send(msg='可以发送“双面”以双面打印', toUserName=val['user_requests'][0][0])
        itchat.send('@img@QRs/%.2f.jpg' % val['user_requests'][0][2], toUserName=val['user_requests'][0][0])
        logging.info('QR image sent')
        val['submit_time'] = time.time()
        val['status'] = 1


def split_file():
    global val
    pdfFileWriter1 = PdfFileWriter()
    pdfFileWriter2 = PdfFileWriter()
    pdfFileReader = PdfFileReader(val['user_requests'][0][1])
    ansacion = pdfFileReader.getNumPages()
    if ansacion == 1:
        return False
    else:
        for i in range(0, (num_pages+1)//2):
            if (i+1) * 2 <= num_pages:
                pageObj2 = pdfFileReader.getPage((-i * 2 - 1)+(num_pages)//2*2)
                pageObj2.rotateClockwise(180)
                pdfFileWriter2.addPage(pageObj2)
            pageObj1 = pdfFileReader.getPage(i * 2)
            pdfFileWriter1.addPage(pageObj1)
        pdfFileWriter1.write(open((val['user_requests'][0][1])[:-4]+'2.pdf', 'wb'))
        pdfFileWriter2.write(open((val['user_requests'][0][1])[:-4]+'1.pdf', 'wb'))
        return True
    

@itchat.msg_register(itchat.content.ATTACHMENT, isFriendChat=True)
def receive_file(msg):
    '''
    处理文件发送请求
    判断是否系统繁忙和文件类型；计算价格；发送二维码并更新全局变量值
    '''
    global val
    logging.info('file received:'+msg.fileName)
    # 获取文件名称
    filename = msg.fileName
    # 判断文件是否为空或者格式不正确
    if not filename or not re.search('\.pdf$', filename):
        logging.warning('user request rejected: "只能接受 pdf 文件呀！"')
        itchat.send(msg='只能接受 pdf 文件呀！', toUserName=msg.fromUserName)
    else:
        logging.warning('user request accepted: "收到文件: "%s"\n正在处理中，请稍后....."' % filename)
        itchat.send(msg='收到文件: "%s"\n正在处理中，请稍后.....' % filename, toUserName=msg.fromUserName)
        # 更新文件名为安全的系统文件名
        filename = os.path.join('uploads', re.sub(r'[^\w\d-]', '_', filename[:-4]) + '.pdf')
        # 下载文件
        msg.text(filename)
        logging.info('file downloaded as <%s>' % filename)
        # 获取PDF页数
        pages = PdfFileReader(filename).getNumPages()
        if pages > 50:
            itchat.send(msg='只能接受不超过50页的文件呀！', toUserName=msg.fromUserName)
        else:
            # 总价格
            price = val['price_per_page'] * pages
            logging.info('price calculated as <%.2f>' % price)
            itchat.send(msg='有其他人正在支付，可能需要稍等%s分钟噢' % int(len(val['user_requests'])/3), toUserName=msg.fromUserName)
            form = 0
            orientation = 0
            val['user_requests'].append((msg.fromUserName, filename, price, form, orientation))
               

@itchat.msg_register(itchat.content.SHARING, isMpChat=True)
def receive_print_file(msg):
    '''
    处理收款到账通知
    判断金额数量是否正确
    '''
    global val
    logging.info('transaction received as <%s>' % msg.text)
    # 判断是否为微信支付消息
    if msg.text[:6] == '[店员消息]':
        # 获取金额
        price = float(msg.text[10:-1])
        transaction_logger.info(price)
        if price >= round(val['user_requests'][0][2],2):
            if val['status'] == 1:
                itchat.send('支付成功，打印中....', toUserName=val['user_requests'][0][0])
                logging.info('payment success as "支付成功，单面打印中...."')
                os.system('.\\gsview\\gsprint.exe ".\\%s"' % val['user_requests'][0][1])
                val['status'] = 0
                del val['user_requests'][0]
            elif val['status'] == 2:
                val['status'] = 4
                if split_file():
                    itchat.send('支付成功，打印正面中....\n待第一面打印完成后，将打印出的纸张直接放到下方纸摞上\n！注意不要改变纸张方向\n放好后发送"继续"以打印反面', toUserName=val['user_requests'][0][0])
                    os.system('.\\gsview\\gsprint.exe ".\\%s"' % (val['user_requests'][0][1])[:-4]+'1.pdf')
                    logging.info('payment success as "支付成功，双面打印中...."')
                    val['status'] = 3
                else:
                    itchat.send('文件只有一页，打印任务转换为单面打印', toUserName=val['user_requests'][0][0])
                    logging.info('payment success as "支付成功，单面打印中...."')
                    os.system('.\\gsview\\gsprint.exe ".\\%s"' % val['user_requests'][0][1])
                    val['status'] = 0
                    del val['user_requests'][0]


@itchat.msg_register(itchat.content.TEXT, isFriendChat=True)
def receive_cancel_message(msg):
    '''
    处理取消打印指令或口令
     '''
    global val
    #判断是否为取消指令或口令
    if msg.text == '取消':
        place = -1
        for n, element in enumerate(val['user_requests']):
            if msg.fromUserName == element[0]:
                place = n
                break
        if place >= 0:
            logging.info('printing cancelled by user')
            itchat.send('打印任务取消成功', toUserName=msg.fromUserName)
            del val['user_requests'][place]
            if place == 0:
                val['status'] = 0
        else:
            logging.warning('printing calcelling failed')
            itchat.send('无可取消的打印任务', toUserName=msg.fromUserName)
    if msg.text == '使用攻略' or msg.text == 'user guide' or msg.text == 'User Guide' or msg.text == 'user_guide':
        itchat.send_file('Files/user_guide.pdf', toUserName=msg.fromUserName)
    if msg.text == '双面' and msg.fromUserName == val['user_requests'][0][0] and val['status'] == 1:
        itchat.send('已收到双面打印请求，请尽快扫码', toUserName=msg.fromUserName)
        val['status'] = 2
    if msg.text == '继续' and msg.fromUserName == val['user_requests'][0][0] and val['status'] == 3:
        itchat.send('打印反面中.....', toUserName=val['user_requests'][0][0])
        os.system('.\\gsview\\gsprint.exe ".\\%s"' % (val['user_requests'][0][1])[:-4]+'2.pdf')
        val['status'] = 0
        del val['user_requests'][0]


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
    
