from price_checker.data_collector import Scrapper
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import requests
import json


class YandexScrapper(Scrapper):
    link = 'https://market.yandex.ru/'

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.product_list = []
        self.filter_url = '123'
        self.json_file = ''

    def collect_product_types(self):
        self.driver.get(self.link)
        search_line = self.driver.find_element(By.ID, 'header-search')
        search_line.send_keys('rtx4070')

        btns = self.driver.find_elements(By.TAG_NAME, 'button')
        btns[2].click()

        # filter
        self.driver.find_element(By.LINK_TEXT, 'Все фильтры').click()
        # находим нужный фильтр
        fs = self.driver.find_elements(By.TAG_NAME, 'h4')

        for i in fs:
            if i.text == 'Название видеокарты':
                i.click()
                break
        # кликаем на нужные флажки
        interesting_product = set()
        fs = self.driver.find_elements(By.CLASS_NAME, '_24XUl')
        for i in fs:
            text = i.get_attribute('value')
            if 'RTX 4070' in text:
                interesting_product.add(text)
        self.product_list = interesting_product
        self.filter_url = self.driver.current_url

        return self.product_list

    def collect_product_list(self):
        final_data = dict()
        for product in self.product_list:
            final_data[product] = dict()
            print('==PRODUCT==')
            print(product)
            self.driver.get(self.filter_url)
            fs = self.driver.find_elements(By.TAG_NAME, 'h4')

            for i in fs:
                if i.text == 'Название видеокарты':
                    i.click()
            # смотрим все варианты и находим нужный
            fs = self.driver.find_elements(By.CLASS_NAME, '_8yOdX')
            target = None
            for i in fs:
                text = i.find_element(By.TAG_NAME, 'input').get_attribute('value')
                if product == text:
                    target = i.find_element(By.TAG_NAME, 'div')
                    break
            # пробуем заселектить
            try:
                self.driver.execute_script("window.scrollTo(0, 500);")
                target.click()
            except Exception as e:
                if 'is not clickable' in str(e):
                    print('cant click')
                else:
                    print(e)
            # подтверждаем фильтр
            for i in self.driver.find_elements(By.TAG_NAME, 'a'):
                if 'Показать' in i.text and 'предлож' in i.text:
                    sleep(3)
                    print(i.text)
                    i.click()
                    break
            # прогружаем все товары
            while True:
                for i in self.driver.find_elements(By.TAG_NAME, 'button'):
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
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight-700);")
            final_data[product]['catalog_url'] = self.driver.current_url
            card_url = set()
            for tag in self.driver.find_elements(By.TAG_NAME, 'a'):
                href = tag.get_attribute('href')
                if 'product' in href and tag.get_attribute('class') == 'egKyN _2Fl2z':  #
                    card_url.add(href)
            final_data[product]['list_urls'] = list(card_url)
            print(len(card_url))
        sleep(10)
        self.driver.quit()
        filename = f'data/data_{self.datetimer()}.json'
        with open(filename, 'w') as f:
            json.dump(final_data, f)
        self.json_file = filename
        return filename

    def save_stats(self):
        stats = []
        with open(self.json_file, 'r') as f:
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
                for i in soup.find_all('div', attrs={'class': 'visuallyhidden'}):
                    if 'капча' in i.text.lower() or 'captcha' in i.text.lower():
                        sleep(10)
                        response = requests.get(link, headers=user_agent)
                        print(response.ok)
                        soup = BeautifulSoup(response.text, 'html.parser')
                name, price, seller, rating, n_repo = [None] * 5
                try:
                    print('start')
                    name = soup.find(attrs={'data-auto': 'productCardTitle'}).text
                    print('name ok')
                    price = soup.find(attrs={'data-auto': 'price-value'})
                    if price is None:
                        price = soup.find(attrs={'data-auto': 'snippet-price-current'}).text
                        price = price[price.find(':') + 1:-2]
                    else:
                        price = price.text
                    print('price ok', price, link)
                    seller = next(soup.find('div', attrs={'data-walter-collection': 'supplierName'}).children).text
                    print('seller ok')
                    rating = soup.find('span', attrs={'aria-hidden': 'true'}).text
                    print('rating ok')
                    n_repo = next(soup.find('div', attrs={'data-zone-name': 'reviews-count'}).children).text
                    print('n_repo ok')
                except AttributeError as e:
                    print('--error--')
                    print(e)
                    name = name or '--error--'
                    price = price or ''
                    seller = seller or ''
                    rating = rating or ''
                    n_repo = n_repo or ''
                    filename = f"data/errors/error_{self.datetimer()}.html"
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                finally:
                    stats.append((name, price, seller, rating, n_repo, link))

        stats = pd.DataFrame(stats, columns=['Name', 'Price', 'Seller', 'Seller-rate', 'Seller-n-rews', 'Link'])
        stats.to_csv(f'data/stats_{self.datetimer()}.csv', index=False)


if __name__ == '__main__':
    scrap = YandexScrapper()
    scrap.collect_product_types()
    scrap.collect_product_list()
    scrap.save_stats()
