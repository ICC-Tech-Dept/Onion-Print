'''
主程序



正式版V1.3

'''

__author__ = '-T.K.-'
__modefier__ = 'DessertFox-M'
__last_modify__ = '5/20/2019'

import itchat
import time
import re
import os
import logging
import datetime
from PyPDF2 import PdfFileReader, PdfFileWriter
import win32print
import win32api

# 全局变量，用于两个消息 handler 之间传值
val = {
    'status': 0,
    'submit_time': 0,
    'dual_submit_time': 0,
    'price_per_page': 0.10,
    'user_requests': [],
    'file_number': 0,
    'color_printer': 'OneNote',
    'black_printer': 'Microsoft Print to PDF',
}

# pdf 页码正则规则
re_pdf_page_pattern = re.compile(r'/Type\s*/Page([^s]|$)', re.MULTILINE | re.DOTALL)

# log 相关设置
logging.basicConfig(level=logging.INFO, filename='%s.log' % datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                    filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.getLogger().addHandler(logging.StreamHandler())
transaction_logger = logging.Logger(__name__)
transaction_logger.addHandler(logging.FileHandler('payment_%s.log' % datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), mode='w'))


win32print.SetDefaultPrinter(val['black_printer'])


def expire_test():
    global val
    if time.time() > (val['submit_time'] + 45) and (val['status'] == 1 or val['status'] == 2):
        logging.info('TIMEOUT - user payment timeout')
        itchat.send(msg='操作超时，请重试', toUserName=val['user_requests'][0][0])
        time.sleep(1)
        val['status'] = 0
        if val['user_requests'][0][3] == 1:
            win32print.SetDefaultPrinter(val['black_printer'])
        del val['user_requests'][0]


def dual_expire_test():
    global val
    if time.time() > (val['dual_submit_time'] + 300) and val['status'] == 3:
        logging.info('TIMEOUT - user payment timeout')
        itchat.send(msg='操作超时，双面打印已取消', toUserName=val['user_requests'][0][0])
        time.sleep(1)
        val['status'] = 0
        if val['user_requests'][0][3] == 1:
            win32print.SetDefaultPrinter(val['black_printer'])
        del val['user_requests'][0]


def qr_send():
    '''
    读取待打印名单发送二维码
    '''
    global val
    if val['user_requests'] != [] and val['status'] == 0 and val['user_requests'][0][2] != 0:
        itchat.send(msg='文件计算后的价格为%.1f元\n请在45秒内扫描下方的二维码唷' % (val['user_requests'][0][2]), toUserName=val['user_requests'][0][0])
        itchat.send(msg='可以在扫码前发送“双面”以双面打印，或“彩色”以彩色打印', toUserName=val['user_requests'][0][0])
        itchat.send('@img@QRs/%.1f.jpg' % val['user_requests'][0][2], toUserName=val['user_requests'][0][0])
        logging.info('QR image sent')
        val['submit_time'] = time.time()
        val['status'] = 1


def split_file():
    global val
    pdfFileWriter1 = PdfFileWriter()
    pdfFileWriter2 = PdfFileWriter()
    pdfFileReader = PdfFileReader(val['user_requests'][0][1])
    num_pages = pdfFileReader.getNumPages()
    if num_pages == 1:
        return False
    else:
        for i in range(0, (num_pages + 1) // 2):
            if (i + 1) * 2 <= num_pages:
                pageObj2 = pdfFileReader.getPage((-i * 2 - 1) + (num_pages) // 2 * 2)
                pageObj2.rotateClockwise(180)
                pdfFileWriter2.addPage(pageObj2)
            pageObj1 = pdfFileReader.getPage(i * 2)
            pdfFileWriter1.addPage(pageObj1)
        pdfFileWriter1.write(open((val['user_requests'][0][1])[:-4] + 'b.pdf', 'wb'))
        pdfFileWriter2.write(open((val['user_requests'][0][1])[:-4] + 'a.pdf', 'wb'))
        return True


@itchat.msg_register(itchat.content.ATTACHMENT, isFriendChat=True)
def receive_file(msg):
    '''
    处理文件发送请求
    判断是否系统繁忙和文件类型；计算价格；发送二维码并更新全局变量值
    '''
    global val
    logging.info('file received:' + msg.fileName)
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
        filename = os.path.join(str(val['file_number']) + '.pdf')
        val['file_number'] += 1
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
            pdf = PdfFileReader(open(filename, 'rb'))
            page = pdf.getPage(0).mediaBox
            if page.getUpperRight_x() - page.getUpperLeft_x() > page.getUpperRight_y() - page.getLowerRight_y():
                pdfFileWriter = PdfFileWriter()
                pdfFileReader = PdfFileReader(filename)
                num_pages = pdfFileReader.getNumPages()
                for i in range(0, num_pages):
                    pageObj = pdfFileReader.getPage(i)
                    if i % 2 == 0:
                        pageObj.rotateClockwise(90)
                    else:
                        pageObj.rotateClockwise(270)
                    pdfFileWriter.addPage(pageObj)
                pdfFileWriter.write(open(filename, 'wb'))
                orientation = 1
            else:
                orientation = 0
            if len(val['user_requests']) != 0:
                Time = len(val['user_requests']) * 45
                if Time > 60:
                    minute = Time // 60
                    second = Time % 60
                    itchat.send(msg=f'有其他人正在支付，可能需要稍等{minute}分{second}秒噢', toUserName=msg.fromUserName)
                else:
                    itchat.send(msg=f'有其他人正在支付，可能需要稍等{Time}秒噢', toUserName=msg.fromUserName)
            form = 0
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
    if msg.text[:6] == '[店员消息]' and len(val['user_requests']) != 0:
        # 获取金额
        price = float(msg.text[10:-1])
        transaction_logger.info(price)
        if price >= round(val['user_requests'][0][2], 2):
            if val['user_requests'][0][3] == 1:
                win32print.SetDefaultPrinter(val['color_printer'])
            if val['status'] == 1:
                if val['user_requests'][0][4] == 1:
                    pdfFileWriter = PdfFileWriter()
                    pdfFileReader = PdfFileReader(val['user_requests'][0][1])
                    num_pages = pdfFileReader.getNumPages()
                    for i in range(0, num_pages):
                        pageObj = pdfFileReader.getPage(i)
                        if i % 2 == 1:
                            pageObj.rotateClockwise(180)
                        pdfFileWriter.addPage(pageObj)
                    pdfFileWriter.write(open(val['user_requests'][0][1], 'wb'))
                itchat.send('支付成功，打印中....', toUserName=val['user_requests'][0][0])
                logging.info('payment success as "支付成功，单面打印中...."')
                win32api.ShellExecute(0, 'print', val['user_requests'][0][1], '/d:"%s"' % win32print.GetDefaultPrinter(), ".", 0)
                time.sleep(15)
                if val['user_requests'][0][3] == 1:
                    win32print.SetDefaultPrinter(val['black_printer'])
                val['status'] = 0
                del val['user_requests'][0]
            elif val['status'] == 2:
                if split_file():
                    itchat.send('支付成功，打印正面中....\n待第一面打印完成后，将打印出的纸张直接放到下方纸摞上\n！注意不要改变纸张方向\n放好后发送"继续"以打印反面', toUserName=val['user_requests'][0][0])
                    win32api.ShellExecute(0, 'print', (val['user_requests'][0][1])[:-4] + 'a.pdf', '/d:"%s"' % win32print.GetDefaultPrinter(), ".", 0)
                    logging.info('payment success as "支付成功，双面打印中...."')
                    val['dual_submit_time'] = time.time()
                    time.sleep(10)
                else:
                    if val['user_requests'][0][4] == 1:
                        pdfFileWriter = PdfFileWriter()
                        pdfFileReader = PdfFileReader(val['user_requests'][0][1])
                        num_pages = pdfFileReader.getNumPages()
                        for i in range(0, num_pages):
                            pageObj = pdfFileReader.getPage(i)
                            if i % 2 == 1:
                                pageObj.rotateClockwise(180)
                            pdfFileWriter.addPage(pageObj)
                        pdfFileWriter.write(open(val['user_requests'][0][1], 'wb'))
                    itchat.send('文件只有一页，打印任务转换为单面打印', toUserName=val['user_requests'][0][0])
                    logging.info('payment success as "支付成功，单面打印中...."')
                    win32api.ShellExecute(0, 'print', val['user_requests'][0][1], '/d:"%s"' % win32print.GetDefaultPrinter(), ".", 0)
                    time.sleep(15)
                    val['status'] = 0
                    if val['user_requests'][0][3] == 1:
                        win32print.SetDefaultPrinter(val['black_printer'])
                    del val['user_requests'][0]


@itchat.msg_register(itchat.content.TEXT, isFriendChat=True)
def receive_cancel_message(msg):
    '''
    处理取消打印指令或口令
     '''
    global val
    # 判断是否为取消指令或口令
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
    if msg.text == '彩色' and msg.fromUserName == val['user_requests'][0][0] and (val['status'] == 1 or val['status'] == 2):
        itchat.send('已收到彩色打印请求，请稍等', toUserName=msg.fromUserName)
        pages = PdfFileReader(val['user_requests'][0][1]).getNumPages()
        price = pages * 0.5
        val['user_requests'][0] = (val['user_requests'][0][0], val['user_requests'][0][1], price, 1, val['user_requests'][0][4])
        itchat.send(msg=f'文件计算后的价格为{price}元\n请在45秒内扫描彩色二维码', toUserName=val['user_requests'][0][0])
        itchat.send(msg='可以在扫码前发送“双面”以双面打印', toUserName=val['user_requests'][0][0])
        itchat.send('@img@ColorQRs/%.2f.jpg' % price, toUserName=val['user_requests'][0][0])
        logging.info('QR image sent')
        val['submit_time'] = time.time()
        win32print.SetDefaultPrinter(val['color_printer'])
    if msg.text == '继续' and msg.fromUserName == val['user_requests'][0][0] and val['status'] == 2:
        itchat.send('打印反面中.....', toUserName=val['user_requests'][0][0])
        win32api.ShellExecute(0, 'print', (val['user_requests'][0][1])[:-4] + 'b.pdf', '/d:"%s"' % win32print.GetDefaultPrinter(), ".", 0)
        time.sleep(15)
        val['status'] = 0
        if val['user_requests'][0][3] == 1:
            win32print.SetDefaultPrinter(val['black_printer'])
        del val['user_requests'][0]


@itchat.msg_register(itchat.content.FRIENDS)
def add_friend(msg):
    itchat.add_friend(**msg['Text'])


logging.info('Logging into itchat...')
itchat.auto_login(hotReload=True)


# 使用 nonblocking 模式单开线程接收消息
itchat.run(blockThread=False)
logging.info('itchat activated and running...')


while True:
    time.sleep(1)
    # 检测交易是否超时
    expire_test()
    dual_expire_test()
    qr_send()
