import socket
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 虚拟机节点配置（请根据实际环境修改IP和端口）
VM_NODES = [
    {"ip": "192.168.1.101", "port": 8888, "status": "online"},
    {"ip": "192.168.1.102", "port": 8888, "status": "online"},
    {"ip": "192.168.1.103", "port": 8888, "status": "online"}
]

# 初始化SQLite数据库：存储任务与发送结果
def init_db():
    conn = sqlite3.connect('imessage_group_send.db')
    cursor = conn.cursor()
    # 创建任务表：记录号码、内容、状态、执行节点等信息
    cursor.execute('''CREATE TABLE IF NOT EXISTS send_tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  phone TEXT NOT NULL UNIQUE,
                  content TEXT NOT NULL,
                  status TEXT DEFAULT 'pending',
                  vm_ip TEXT,
                  create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  send_time TIMESTAMP)''')
    conn.commit()
    conn.close()

# 批量添加待发送任务（支持外部号码列表导入）
def add_task_batch(phone_list, message_content):
    if not phone_list:
        print("待发送号码列表为空")
        return
    
    init_db()
    conn = sqlite3.connect('imessage_group_send.db')
    cursor = conn.cursor()
    
    # 过滤重复号码
    task_data = []
    for phone in phone_list:
        cursor.execute("SELECT id FROM send_tasks WHERE phone=?", (phone,))
        if not cursor.fetchone():
            task_data.append((phone, message_content))
    
    if task_data:
        cursor.executemany("INSERT INTO send_tasks (phone, content) VALUES (?, ?)", task_data)
        conn.commit()
        print(f"成功添加{len(task_data)}条新任务（已过滤重复号码）")
    else:
        print("无新任务可添加")
    conn.close()

# 更新任务发送状态
def update_task_status(task_id, status, vm_ip):
    send_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect('imessage_group_send.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE send_tasks SET status=?, vm_ip=?, send_time=? WHERE id=?",
        (status, vm_ip, send_time, task_id)
    )
    conn.commit()
    conn.close()

# 单个任务发送：分配到指定虚拟机节点
def send_single_task(vm_node, task_id, phone, content):
    vm_ip = vm_node["ip"]
    vm_port = vm_node["port"]
    try:
        # 与虚拟机建立Socket连接
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(15)  # 设置超时时间，避免阻塞
        client_socket.connect((vm_ip, vm_port))
        
        # 发送任务指令
        task_cmd = f"{phone}|{content}".encode('utf-8')
        client_socket.send(task_cmd)
        
        # 接收发送结果
        result = client_socket.recv(1024).decode('utf-8').strip()
        if result.startswith("True"):
            update_task_status(task_id, "success", vm_ip)
            print(f"任务{task_id}：号码{phone} 发送成功（执行节点：{vm_ip}）")
        else:
            err_msg = result.split('|')[1] if "|" in result else "未知错误"
            update_task_status(task_id, "fail", vm_ip)
            print(f"任务{task_id}：号码{phone} 发送失败 - {err_msg}（执行节点：{vm_ip}）")
        
        client_socket.close()
    except Exception as e:
        update_task_status(task_id, "fail", vm_ip)
        print(f"任务{task_id}：号码{phone} 执行异常 - {str(e)}（执行节点：{vm_ip}）")

# 核心调度逻辑：任务均匀分配到在线虚拟机
def task_scheduler():
    init_db()
    # 筛选在线虚拟机节点
    online_vms = [vm for vm in VM_NODES if vm["status"] == "online"]
    if not online_vms:
        print("暂无在线虚拟机节点，调度终止")
        return
    
    # 获取待发送任务
    conn = sqlite3.connect('imessage_group_send.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, phone, content FROM send_tasks WHERE status='pending' LIMIT 500")
    pending_tasks = cursor.fetchall()
    conn.close()
    
    if not pending_tasks:
        print("暂无待发送任务")
        return
    
    print(f"本次调度待发送任务数：{len(pending_tasks)} | 在线虚拟机数：{len(online_vms)}")
    # 多线程执行任务，提升调度效率
    with ThreadPoolExecutor(max_workers=len(online_vms)) as executor:
        for task_idx, task in enumerate(pending_tasks):
            task_id, phone, content = task
            # 轮询分配任务，确保负载均衡
            target_vm = online_vms[task_idx % len(online_vms)]
            executor.submit(send_single_task, target_vm, task_id, phone, content)

if __name__ == "__main__":
    # 示例：添加测试任务
    test_phone_list = ["+12025550101", "+12025550102", "+12025550103"]
    test_content = "【合规测试】iMessage虚拟机集群群发系统测试消息，请勿回复"
    add_task_batch(test_phone_list, test_content)
    
    # 启动周期性调度（每15秒执行一次）
    while True:
        task_scheduler()
        time.sleep(15)