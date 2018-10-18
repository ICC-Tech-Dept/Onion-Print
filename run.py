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

# 全局变量，用于两个消息 handler 之间传值
val = {
    'status': 0,
    'username': None,
    'price': 0,
    'submit_time': 0,
    'price_per_page': 0.20,
    }

# pdf 页码正则规则
re_pdf_page_pattern = re.compile(r'/Type\s*/Page([^s]|$)', re.MULTILINE|re.DOTALL)

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
        itchat.send(msg='操作超时，请重试', toUserName=val['username'])
        val['status'] = 0


@itchat.msg_register(itchat.content.ATTACHMENT, isFriendChat=True)
def receive_file(msg):
    '''
    处理文件发送请求
    判断是否系统繁忙和文件类型；计算价格；发送二维码并更新全局变量值
    '''
    global val
    print('file received:', msg.fileName)
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

            itchat.send(msg='计算后的价格为 %.2f\n请在60秒内扫描下方的二维码唷' % price, toUserName=msg.fromUserName)
            itchat.send('@img@QRs/%.2f.jpg' % price, toUserName=msg.fromUserName)

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
    print('transaction received:', msg.text)
    
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
    expire_test()
