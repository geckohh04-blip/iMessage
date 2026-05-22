import objc
from Foundation import NSURL
from Messages import *
import socket
import threading

# 初始化iMessage原生接口
def init_imessage_sender():
    try:
        objc.loadBundle('Messages', bundle_path='/System/Library/Frameworks/Messages.framework', module_globals=globals())
        return True
    except Exception as e:
        print(f"iMessage接口初始化失败：{str(e)}")
        return False

# 单条iMessage发送核心函数
def send_imessage(phone_number, message_content):
    # 校验号码格式（海外号码需带国家码，如+1、+44）
    if not phone_number.startswith("+"):
        return False, "号码格式错误，需带国家码（如+12025550101）"
    
    if not init_imessage_sender():
        return False, "iMessage接口初始化失败"
    
    try:
        # 构建iMessage收件人URL
        recipient_url = NSURL.URLWithString_(f"tel:{phone_number}")
        if not recipient_url:
            return False, "收件人URL构建失败"
        
        # 创建消息请求对象
        message_request = MSMessageRequest.alloc().init()
        message_request.setRecipients_([recipient_url])
        message_request.setMessageText_(message_content)
        
        # 同步发送消息
        error = None
        message_request.sendSynchronouslyWithError_(error)
        return True, "发送成功"
    except Exception as e:
        return False, f"发送失败：{str(e)}"

# Socket服务端：与主机端建立通信，接收调度任务
def start_socket_server(host='0.0.0.0', port=8888):
    if not init_imessage_sender():
        return
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"虚拟机iMessage服务已启动，监听端口：{port}")
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"成功连接主机：{addr}")
            # 接收主机端指令：格式为 手机号码|消息内容
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data or "|" not in data:
                client_socket.send("False|指令格式错误，需为 号码|内容".encode('utf-8'))
                client_socket.close()
                continue
            
            phone, content = data.split('|', 1)
            success, msg = send_imessage(phone, content)
            # 向主机端返回发送结果
            client_socket.send(f"{success}|{msg}".encode('utf-8'))
            client_socket.close()
        except Exception as e:
            print(f"通信异常：{str(e)}")
            continue

if __name__ == "__main__":
    # 启动虚拟机端发送服务
    start_socket_server()