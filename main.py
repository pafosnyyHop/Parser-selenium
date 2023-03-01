import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm.session import sessionmaker
from decouple import config


engine = create_engine(f"postgresql+psycopg2://{config('USERNAME')}:{config('PASSWORD')}@{config('HOST')}/{config('DB_NAME')}", echo=True)
base = declarative_base()
session = sessionmaker(bind=engine)()


class Apartament(base):
    __tablename__= 'apartaments'
    id = Column(Integer, primary_key=True)
    image = Column(String)
    price = Column(String)
    currency = Column(String)
    date = Column(String)

    def __repr__(self) -> str:
        return f'{self.price}'


def get_source_html(url):
    """Парсер c requests"""

    try:
        time.sleep(3)
        response = requests.get(url)

        with open('source-page.html', 'w') as file:
            file.write(response.text)

    except Exception as ex:
        print(ex)


def get_source_html_selenium(url):
    """Парсер с селениумом"""
    driver = webdriver.Chrome(
        executable_path='/home/hello/Рабочий стол/modul/parser/chromedriver/chromedriver',
    )

    try:
        driver.get(url=url)
        time.sleep(3)

        with open('source-page.html', 'w') as file:
            file.write(driver.page_source)

    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


def get_cards(file_path) -> bool:
    """
    функция парсер, получает все данные с сайта
    """
    with open(file_path) as file:
        html = file.read()
    soup = BeautifulSoup(html, 'html.parser')
    items_divs = soup.find_all('div', class_='container-results')
    cards = items_divs[-1].find_all('div', {'class': 'clearfix'})
    try:
        next = soup.find('div', class_='bottom-bar').find('div', class_='pagination').find('a', title='Next')

        for card in cards:

            bad_price = card.find('div', class_='price').text.strip()
            bad_date = card.find('div', class_='location').find('span', class_='date-posted').text

            try:
                image = card.find('div', class_='image').find('img').get('data-src')
            except:
                image = 'NO IMAGE! :p'

            if bad_price.find('$'):
                price = 'None'
                currency = 'None'
            else:
                currency = bad_price[0]
                price = bad_price.replace('$', '')

            if bad_date.find('ago') != -1:
                date = f'{datetime.now().day}/{datetime.now().month}/{datetime.now().year}'
            else:
                date = bad_date

            data = {
            'image': image,
            'price': price,
            'currency': currency,
            'date': date
            }
            # print(data)
            session.add_all([Apartament(image=image, price=price, currency=currency, date=date)])
            session.commit()

        return True

    except Exception:
        return False

    
def main():
    base.metadata.create_all(engine)
    i = 1

    while True:
        url = f'https://www.kijiji.ca/b-apartments-condos/city-of-toronto/page-{i}/c37l1700273?ad=offering'
        get_source_html(url)
        is_res = get_cards(file_path='source-page.html')
        if not is_res:
            break
        print(f'Страница: {i}')
        i += 1


if __name__ == '__main__':
    main()
