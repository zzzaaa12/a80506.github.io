import requests
import time
import atexit
import signal
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

LINE_NOTIFY_TOKEN = ''  # 請填入您的LINE Notify令牌
PCNAME = 'TestPC'
START_DELAY_SEC = 30
INTERVAL_MIN = 10

# 獲取對外IP地址的函數
def get_external_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        ip = response.json()['ip']
        return ip
    except Exception as e:
        return f"Error getting IP: {e}"

# 發送Line通知的函數
def send_line_notify(message):
    try:
        token = LINE_NOTIFY_TOKEN
        line_notify_api = 'https://notify-api.line.me/api/notify'
        headers = {'Authorization': f'Bearer {token}'}
        data = {'message': message}
        requests.post(line_notify_api, headers=headers, data=data)
    except Exception as e:
        print(f"Error sending LINE Notify: {e}")

# 檢查IP變更並發送通知的函數
def check_and_notify_ip_change(scheduler):
    global last_ip
    current_ip = get_external_ip()
    if current_ip != last_ip and current_ip.startswith('Error') is False:
        last_ip = current_ip
        send_line_notify(f'{PCNAME}\nIP Changed: {current_ip}')

# 每日定時發送當前時間的函數
def send_daily_time():
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        send_line_notify(f"{PCNAME}\nCurrent Time: {current_time}")
    except Exception as e:
        print(f"Error in send_daily_time: {e}")

# 程式退出時執行的函數
def on_exit():
    send_line_notify(f"{PCNAME} has stopped running.")

# 註冊退出時要執行的函數
atexit.register(on_exit)

# 處理特定信號的函數
def signal_handler(signum, frame):
    send_line_notify(f"Program terminated by signal: {signum}")
    sys.exit(1)

# 註冊信號處理器
signal.signal(signal.SIGINT, signal_handler)  # 處理 Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # 處理終止信號

try:
    time.sleep(START_DELAY_SEC)

    # 初始化全局變量來儲存上一次的IP地址
    last_ip = get_external_ip()
    if last_ip.startswith('Error') is False:
        print(last_ip)
        send_line_notify(f'{PCNAME}\nIP start: {last_ip}')

    # 創建並啟動排程器
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_notify_ip_change, 'interval', minutes=INTERVAL_MIN, args=[scheduler])
    scheduler.add_job(send_daily_time, 'cron', hour=8, minute=0)
    scheduler.start()

    # 等待直到排程任務完成或程序被手動中斷
    scheduler.print_jobs()
    scheduler._event.wait()  # 使用事件等待來代替無窮迴圈

except Exception as e:
    send_line_notify(f"Program terminated due to an exception: {e}")
    print(f"Unexpected error: {e}")
    raise
finally:
    if 'scheduler' in locals() and scheduler.running:
        scheduler.shutdown()
