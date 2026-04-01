import base64
import csv
import hashlib
import hmac
import os
import re
import time
from datetime import datetime
from time import sleep

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_browser_options():
    options = webdriver.EdgeOptions()
    options.add_argument('--headless')                                          # 无头模式, 即无界面操作
    options.add_argument('--disable-gpu')                                       # 禁用GPU加速
    options.add_argument('--disable-blink-features=AutomationControlled')       # 实现规避检测
    options.add_experimental_option('excludeSwitches', ['enable-logging'])      # 禁止输出edge浏览器日志
    options.add_argument('--start-maximized')                                   # 最大化，方便后面js脚本运行
    options.add_experimental_option("excludeSwitches", ["enable-automation"])   # 禁用浏览器正在被自动化程序控制的提示
    options.add_argument('--ignore-certificate-errors')                         # 添加为启动选项来忽略不受信任的证书错误
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
        )
    options.add_argument('--log-level=3')                                       # 禁止输出一大串日志
    return options

def get_driver():
    options = get_browser_options()
    # service = Service(EdgeChromiumDriverManager().install())
    # driver = webdriver.Edge(service=service, options=options)  # 自动识别浏览器版本下载驱动
    driver = webdriver.Edge(options = options)
    driver.implicitly_wait(60)  # 全局最大等待时间
    return driver

def get_data(driver):
    
    driver.get(f'http://sqk.ziboshuiwen.com/')

    sleep(1)
    driver.refresh()
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))

    # 1. 获取所有 iframe
    iframes = driver.find_elements(By.TAG_NAME, "iframe")

    # 2. 切换到第一个 iframe
    driver.switch_to.frame(iframes[0])

    # 获取页面元素
    span = driver.find_element(By.CLASS_NAME, "value")
    inner_html = span.get_attribute("innerHTML")

    pattern = r"\[.*?岔河.*?\]水位:(\d+(\.\d+)?)[^，]*，流量:(\d+(\.\d+)?)"
    match = re.search(pattern, inner_html)
    
    # 获取当前日期和时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if match:
        water_level = match.group(1)
        flow_rate = match.group(3)
        message_content = f"岔河 水位: {water_level}，流量: {flow_rate}"
        print(message_content)
        # 成功匹配时，返回所需的所有数据
        return message_content, current_time, water_level, flow_rate
    else:
        message_content = "未找到“岔河”的数据"
        print(message_content)
        # 未匹配时，返回 None 以供后续判断
        return message_content, current_time, None, None

def create_sign(secret, timestamp):
    """生成签名"""
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign

def send_dingtalk_message_with_sec(webhook_url, secret, message):
    timestamp = str(round(time.time() * 1000))
    sign = create_sign(secret, timestamp)
    
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    data = {
        "msgtype": "text",
        "text": {
            "content": message
        },
        "timestamp": timestamp,
        "sign": sign
    }
    
    url_with_sec = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
    response = requests.post(url_with_sec, json=data, headers=headers)
    
    if response.status_code == 200:
        print("消息发送成功")
    else:
        print(f"消息发送失败，错误码：{response.status_code}")

def save_to_csv(filename, date_str, water_level, flow_rate):
    """将数据保存到CSV文件"""
    # 检查文件是否存在，用来决定是否需要写入表头
    file_exists = os.path.isfile(filename)
    
    # 使用 utf-8-sig 编码可以防止在 Excel 中打开时中文乱码
    with open(filename, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            # 首次创建文件时，写入表头
            writer.writerow(['记录时间', '监测点', '水位', '流量'])
            
        writer.writerow([date_str, '岔河', water_level, flow_rate])
        print(f"数据已成功写入 {filename}")

def main():
    webhook_base_url = os.getenv("webhook_base_url")
    secret = os.getenv("secret")

    driver = get_driver()
    
    # 获取数据，这里解包返回的四个变量
    message_content, current_time, water_level, flow_rate = get_data(driver)
    
    # 如果成功获取到了水位和流量，就写入 CSV
    if water_level is not None and flow_rate is not None:
        csv_filename = "water_data.csv" # 你可以自定义保存的文件名或路径
        save_to_csv(csv_filename, current_time, water_level, flow_rate)

    # 推送钉钉消息
    if webhook_base_url and secret:
        send_dingtalk_message_with_sec(webhook_base_url, secret, message_content)
    else:
        print("未配置 webhook_base_url 或 secret，跳过钉钉推送。")

    driver.close()
    driver.quit()

if __name__ == '__main__':
    main()

