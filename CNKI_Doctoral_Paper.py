import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import json


def webserver(download_dir="C:/Users/11939/Downloads"):  # 可以传入下载路径
    desired_capabilities = DesiredCapabilities.EDGE
    desired_capabilities["pageLoadStrategy"] = "none"

    options = webdriver.EdgeOptions()
    options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 1,  # y运行加载图片
        "download.default_directory": download_dir,  # 设置默认下载路径
        "download.prompt_for_download": False,  # 禁止下载时弹出提示
        "download.directory_upgrade": True  # 自动下载到指定文件夹
    })

    driver = webdriver.Edge(options=options)
    return driver


def open_page(driver, keyword):
    driver.get("https://kns.cnki.net/kns8/AdvSearch")
    time.sleep(30)

    opt = driver.find_element(By.CSS_SELECTOR, 'div.sort-list')  # 展开排序选项
    driver.execute_script("arguments[0].setAttribute('style', 'display: block;')", opt)  # 展开排序选项

    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.XPATH, '''//*[@id="gradetxt"]/dd[1]/div[2]/input'''))
    ).send_keys(keyword)  # 输入关键词
    time.sleep(5)

    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located(
            (By.XPATH, '''//*[@id="ModuleSearch"]/div[1]/div/div[2]/div/div[1]/div[1]/div[2]/div[3]/input'''))
    ).click()  # 点击搜索按钮
    time.sleep(5)

    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.XPATH, '//a[@name="classify" and @resource="DISSERTATION"]'))
    ).click()  # 选择学位类型为博士论文
    time.sleep(5)

    element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="CF"]'))
    )
    element.click()  # 点击复选框“被引”按钮

    print("正在搜索，请稍后...")

    res_unm = WebDriverWait(driver, 100).until(EC.presence_of_element_located(
        (By.XPATH, '''//*[@id="countPageDiv"]/span[1]/em'''))
    ).text  # 获取结果总数

    res_unm = int(res_unm.replace(",", ''))  # 去除逗号
    page_unm = int(res_unm / 20) + 1  # 计算总页数
    print(f"共找到 {res_unm} 条结果, {page_unm} 页。")
    return res_unm


def crawl(driver, papers_need, theme):
    count = 1

    file_path = f"CNKI1_{theme}_Doctoral_Papers.json"
    data = []

    # 如果JSON文件存在，则读取数据并设置count
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r", encoding='utf-8') as file:
            data = json.load(file)
            if data:
                count = data[-1].get("count", 1) + 1  # 如果JSON中没有count字段，则设置为1

    for page in range(papers_need):  # 循环爬取指定数量的页面
        for i in range(count // 20):  # 循环爬取每页的20条记录
            time.sleep(3)
            # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id='PageNext']"))).click()
            # 点击下一页按钮
            driver.execute_script("arguments[0].click();", WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='PageNext']"))
            ))
        print(f"从第 {count} 条开始爬取\n")

        while count <= (page + 1) * 20:
            time.sleep(3)
            # 获取标题列表
            title_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "fz14")))

            for i in range((count - 1) % 20 + 1, 21):  # 循环爬取每页的20条记录

                print(f"\n-------------正在爬取第 {count} 条(本页第{i}条)-------------\n")

                try:
                    # term = (count - 1) % 20 + 1

                    print('正在获取标题...')
                    title = title_list[i - 1].text.strip()
                    print(f"标题: {title}\n")

                    title_list[i - 1].click()  # 点击标题

                    n = driver.window_handles  # 获取当前窗口句柄

                    driver.switch_to.window(n[-1])  # 切换到新窗口
                    time.sleep(3)

                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '''//*[@id="ChDivSummaryMore"]'''))
                        ).click()  # 点击摘要按钮
                    except:
                        pass

                    print('正在获取文章的摘要：')
                    try:
                        abstract = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "abstract-text"))).text.strip()  # 获取摘要
                    except:
                        abstract = '无'
                    print(f"摘要: {abstract}\n")

                    pdf_download_link = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "pdfDown")))
                    pdf_download_link.click()
                    time.sleep(3)

                    print(f'正在下载标题为"{title}"的PDF文件...')

                    paper_data = {
                        "title": title,
                        "abstract": abstract
                    }

                    data.append(paper_data)

                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                            print('内容写入成功')
                    except Exception as e:
                        print('内容写入失败:', str(e))
                        raise e
                except:
                    print(f" 第{count} 条爬取失败\n")
                    #continue
                    # 获取并输出当前页面的URL
                    current_url = driver.current_url
                    print(f"当前页面的URL为: {current_url}")
                    # 暂停代码执行，等待人工操作
                    input("请进行人工操作后按 Enter 键继续：")
                finally:
                    n2 = driver.window_handles
                    if len(n2) > 1:
                        driver.close()
                        driver.switch_to.window(n2[0])
                    count += 1
                    if count > (page + 1) * 20:  # 判断是否爬取到达当前页的最后一条记录
                        break

            if count > (page + 1) * 20:  # 判断是否爬取到达当前页的最后一条记录
                break
            # 1、点击下一页按钮
            # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@id='PageNext']"))).click()

            # 2、使用 JavaScript 点击下一页按钮
            driver.execute_script("arguments[0].click();", WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='PageNext']"))
            ))

            # 3、显式等待下一页按钮出现
            """
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='PageNext']"))
            )
            element.click()
            """

    print("文章内容爬取完毕！")


if __name__ == "__main__":
    keyword = "breast cancer"
    download_path = r"D:\MyDesktop\Cancer_Dataset\breast_cancer引用排行"  # 修改为你希望的路径
    driver = webserver(download_path)
    papers_need = 100
    res_unm = open_page(driver, keyword)

    papers_need = papers_need if (papers_need <= res_unm) else res_unm

    crawl(driver, papers_need, keyword)

    driver.close()
