'''
主程序
状态：未完成
'''

__author__ = '-T.K.-'
__last_modify__ = '10/18/2018'

import itchat
import time
import re
import os
from pyPDF import PdfFileReader
# 全局变量，用于两个消息 handler 之间传值
val = {
    'status': 0,
    'username': None,
    'price': 0,
    'submit_time': 0,
    }


def calculate_price(filepath):
    '''
    读取 pdf 页数计算价格
    '''
    pdfFileProcessor = PdfFileReader(file(filepath,"rb"))
    #获取PDF页数
    pagesInPdfFile = pdfFileProcessor.getDocumentInfo().getNumPages()
    #总价格
    totalPrice = val['price'] * pagesInPdfFile
    return totalPrice

def expire_text():
    '''
    测试是否超时 60 秒
    '''
    # TODO: 补充逻辑
    statement = None

    if statement and statement > 60:
        itchat.send(msg='操作超时，请重试', toUserName=val['username'])
        val['status'] = 0


@itchat.msg_register(itchat.content.ATTACHMENT, isFriendChat=True)
def receive_file(msg):
    '''
    处理文件发送请求
    判断是否系统繁忙和文件类型；计算价格；发送二维码并更新全局变量值
    '''
    global val
    if val['status'] != 0:
        itchat.send(msg='系统繁忙，有其他人正在打印，请稍等 1 分钟噢', toUserName=msg.fromUserName)
    else:
        # 获取文件名称
        filename = msg.fileName

        # 判断文件是否为空或者格式不正确
        if not filename or not re.search('\.pdf$', filename):
            itchat.send(msg='只能接受 pdf 文件呀！', toUserName=msg.fromUserName)

        else:
            itchat.send(msg='收到文件: "%s"\n正在处理中，请稍后.....' % filename, toUserName=msg.fromUserName)

            # 更新文件名为安全的系统文件名
            filename = os.path.join('uploads', re.sub(r'[^\w\d-]', '_', filename[:-4]) + '.pdf')

            # 下载文件
            msg.text(filename)

            # 计算价格
            price = calculate_price(filename)

            itchat.send(msg='计算后的价格为 %s\n请在60秒内扫描下方的二维码唷' % str(price), toUserName=msg.fromUserName)
            itchat.send('@img@QRs/%s.jpg' % str(price).replace('.', '_'), toUserName=msg.fromUserName)

            val['status'] = 1
            val['username'] = msg.fromUserName
            val['price'] = price
            val['submit_time'] = time.time()


@itchat.msg_register(itchat.content.SHARING, isMpChat=True)
def receive_print_file(msg):
    '''
    处理收款到账通知
    判断金额数量是否正确（其实不需要）
    '''
    global val

    # 判断是否为微信支付消息
    if msg.text[:4] == '微信支付' and val['status'] == 1:

        # 获取金额
        price = float(msg.text[6:-1])
        if price == val['price']:
            itchat.send('支付成功，打印中....', toUserName=val['username'])
        else:
            itchat.send('系统错误，请联系管理员', toUserName=val['username'])
    val['status'] == 0


itchat.auto_login(hotReload=True)

# 使用 nonblocking 模式单开线程接收消息
itchat.run(blockThread=False)
print('running....')

while True:
    time.sleep(1)

    # 检测交易是否超时
    expire_text()
