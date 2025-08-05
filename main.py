import re
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    driver.implicitly_wait(3)  # 全局最大等待时间
    return driver

def get_data(driver):
    
    driver.get(f'http://sqk.ziboshuiwen.com/')

    sleep(1)
    driver.refresh()
    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))

    # 1. 获取所有 iframe
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    # print(f"页面中共有 {len(iframes)} 个 iframe")

    # 2. 切换到第一个 iframe（你可以根据实际情况选择正确的）
    driver.switch_to.frame(iframes[0])  # 或 driver.switch_to.frame("iframe的id或name")

    # 3. 获取并打印页面 HTML，确认是否在 iframe 中能找到目标内容
    # html = driver.page_source

    span = driver.find_element(By.CLASS_NAME, "value")
    inner_html = span.get_attribute("innerHTML")

    pattern = r"\[.*?岔河.*?\]水位:(\d+(\.\d+)?)[^，]*，流量:(\d+(\.\d+)?)"
    match = re.search(pattern, inner_html)
    if match:
        water_level = match.group(1)
        flow_rate = match.group(3)
        print(f"岔河 水位: {water_level}，流量: {flow_rate}")
    else:
        print("未找到“岔河”的数据")

def main():
    driver = get_driver()
    get_data(driver)
    # sleep(60)  # 间隔一分钟刷新一次
    driver.close()
    driver.quit()

if __name__ == '__main__':
    main()


