from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import requests
import json


def prepare_scrapping():
    link = 'https://market.yandex.ru/'

    driver = webdriver.Chrome()

    driver.get(link)

    search_line = driver.find_element(By.ID, 'header-search')
    search_line.send_keys('rtx4070')

    btns = driver.find_elements(By.TAG_NAME, 'button')

    btns[2].click()

    # filter
    driver.find_element(By.LINK_TEXT, 'Все фильтры').click()
    # находим нужный фильтр
    fs = driver.find_elements(By.TAG_NAME, 'h4')

    for i in fs:
        if i.text == 'Название видеокарты':
            i.click()
            break
    filter_page = driver.current_url
    # кликаем на нужные флажки
    interesting_product = set()
    fs = driver.find_elements(By.CLASS_NAME, '_24XUl')
    for i in fs:
        text = i.get_attribute('value')
        if 'RTX 4070' in text:
            interesting_product.add(text)

    return driver, interesting_product, filter_page


def collect_product_proposal(driver, products, filter_url):
    final_data = dict()
    for product in products:
        final_data[product] = dict()
        print('==PRODUCT==')
        print(product)
        driver.get(filter_url)
        fs = driver.find_elements(By.TAG_NAME, 'h4')

        for i in fs:
            if i.text == 'Название видеокарты':
                i.click()
        # смотрим все варианты и находим нужный
        fs = driver.find_elements(By.CLASS_NAME, '_8yOdX')
        target = None
        for i in fs:
            text = i.find_element(By.TAG_NAME, 'input').get_attribute('value')
            if product == text:
                target = i.find_element(By.TAG_NAME, 'div')
                break
        # пробуем заселектить
        try:
            driver.execute_script("window.scrollTo(0, 500);")
            target.click()
        except Exception as e:
            if 'is not clickable' in str(e):
                print('cant click')
            else:
                print(e)
        # подтверждаем фильтр
        for i in driver.find_elements(By.TAG_NAME, 'a'):
            if 'Показать' in i.text and 'предлож' in i.text:
                sleep(3)
                i.click()
                break
        # прогружаем все товары
        while True:
            for i in driver.find_elements(By.TAG_NAME, 'button'):
                try:
                    j = i.find_element(By.TAG_NAME, 'span')
                except Exception as e:
                    pass
                if j and j.text == "Показать ещё":
                    sleep(5)
                    i.click()
                    break
            else:
                break
        final_data[product]['catalog_url'] = driver.current_url
        card_url = set()
        for tag in driver.find_elements(By.TAG_NAME, 'a'):
            href = tag.get_attribute('href')
            if 'product' in href:
                card_url.add(href)
        final_data[product]['list_urls'] = list(card_url)
        print(len(card_url))
    sleep(10)
    driver.quit()
    with open('data/data.json', 'w') as f:
        json.dump(final_data, f)
    return final_data


def parse_list(url):
    stats = []
    with open('data/data.json', 'r') as f:
        d = json.load(f)
    user_agent = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    for i in d.keys():
        for link in d[i]['list_urls']:
            response = requests.get(link, headers=user_agent)
            print(response.ok)
            soup = BeautifulSoup(response.text, 'html.parser')
            with open('data/page.html', 'wb') as f:
                f.write(response.content)
            try:
                print('start')
                name = soup.find(attrs={'data-auto': 'productCardTitle'}).text
                print('name ok')
                price = soup.find(attrs={'data-auto': 'price-value'}).text
                print('price ok')
                seller = next(soup.find('div', attrs={'data-walter-collection': 'supplierName'}).children).text
                print('seller ok')
                rating = soup.find('span', attrs={'aria-hidden': 'true'}).text
                print('rating ok')
                n_repo = next(soup.find('div', attrs={'data-zone-name': 'reviews-count'}).children).text
                print('n_repo ok')
                stats.append((name, price, seller, rating, n_repo, link))
            except AttributeError as e:
                print('--error--')
                print(e)
                stats.append(('--error--', '', '', '', '', link))
                o = input('Go on?')
                if o == 'n':
                    print(link)
                    return 1
    stats = pd.DataFrame(stats, columns=['Name', 'Price', 'Seller', 'Seller-rate', 'Seller-n-rews', 'Link'])
    stats.to_csv('data/stats.csv', index=False)



def parse_list2(driver):
    pass


from time import time
timer = time()
# d, p, u = prepare_scrapping()
# collect_product_proposal(d, p, u)
url = "https://market.yandex.ru/catalog--videokarty/26912670/list?rs=eJwdkD8PwWAYxNuwiFiMYmgMLCQiERIaHUxi8A00RrMPUI0wqMRmkryLxUJiEf_axYpGxFo2E3aD3i2_PLnneve8zZmBhnyUJTFTwdAOHGI2fmWfTn_v03OhKBnM-oXbICg9oTjtEjxxbiOgRqcw-VUBOVIH9Or0TKHrFnMm0EWXenoLZtnYw1Z7Y6uruEoZoEW8NphbNjwn3mCx64rZWTPTgN-pMmFEPYEc7cu0Jd94h-410SiibGwybc47Ywfk1KhXQOXBm2Xyg0uUMXK0Iuid6cnzH6bYe-OrV_wbLhttKmEoxoJdErdJ9Q8Or4uf&text=rtx%204070&hid=91031&allowCollapsing=1&local-offers-first=0&glfilter=36036031%3A50061568&page=2"

parse_list(url)
print(time() - timer)

# Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

# print(url+"/product--videokarta-asus-geforce-rtx-4070-dual-oc-white-12-gb-dual-rtx4070-o12g-white/1885036899?show-uid=17056016189028239203016025&context=search&glfilter=36036031%3A50061568&text=rtx%204070&uniqueId=895199&sku=102062607792&cpc=caJIRDf59vp7tSnjx63Q_UOR6o80L0mbUA24iSy7z6KSzrDMutxy_D9g9f4WfAWPtMqaO1x8BZ8kLCj67sljgfhBIxer9LEX9KomUIWWSILkBc5whX4P9Xqm_XmoQACIpskrYcjXXe4aIFtuop4N-5TIYcmxgLIQ&do-waremd5=D3Xpb6uF4zOVYX2-0BLtdA&rs=eJx9UL8vQ1EYvbca2idNXkz1ariRoAOJVoSg8SImMfgPXl-rotIg_bFXIwwqsZkkbxFhIbE0qL7FikaE8bGZsBv0nIiYLCdfzjnfOd-98UrbgryRwjlMAINXwB3M5a-pFrpb9RZ6TTBqCHPynqofKF7BuCuT8PRQDQFNOp0Kt8aQI4pAb56eA_DJKnP2wTsb5AcvgcNs3IRqvkNNJnCV2kaL83aBOdWA55Y3VNn1gNmtMbMMvzvLhF3yvcgxP5l2xjc-gfcsNDpdbLSYdsI7jWvkzJGfBqoX3iyJH7hE7SHHHAd6d_SM8g8H2PvIV5_zN5psbJDpBFM-ZZeg2p-YOZJatxYISF2GpZK6z-hYzCzZpVxRiajQIi1J6CIslNDbjeCPZMV_RamrcJ_S_ooj_23GKMa4GQiHlF_XjUjKLmTTVtrOr5UKmZy1nrOzq1YhY-fTy-r4ORit1yZ03zcBa63i")