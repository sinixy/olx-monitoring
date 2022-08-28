import requests
import datetime
from bs4 import BeautifulSoup as bs
from utils import async_wrap


headers = {
	"accept": "*/*",
	"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36 OPR/60.0.3255.170"
}

def get_page_data(url):
	page_data = []
	session = requests.Session()
	request = session.get(url, headers=headers)
	soup = bs(request.content, 'lxml')
	wraps = soup.find_all('tr', attrs={'class': 'wrap'})
	for wrap in wraps:
		try:
			loc_date = wrap.find('td', attrs={'class': 'bottom-cell'}).text.strip()
			if 'Сегодня' in loc_date or 'Сьогодні' in loc_date:
				title_container = wrap.find('a', attrs={'data-cy': 'listing-ad-title'})
				href = title_container['href'].strip()
				title = title_container.text.strip()
				price = wrap.find('p', attrs={'class': 'price'}).text.strip()
				page_data.append({
					'title': title,
					'url': href,
					'price': price,
					'date': loc_date.split(' ')[-1]
				})
		except Exception as e:
			print(f'{datetime.datetime.now()} Iteration Error: {e}')
			continue
	return page_data


@async_wrap
def olx_parse(base_url):
	start = datetime.datetime.now()
	urls = []
	urls.append(base_url)
	ads = []
	#использую сессию
	session = requests.Session()
	request = session.get(base_url.replace(' ', ''), headers=headers)
	#проверка ответа от сервера
	if request.status_code == 200:
		soup = bs(request.content, "lxml")
		try:
			#определение последней страницы
			last_page = soup.find('a', attrs={'data-cy': 'page-link-last'})
			if last_page:
				number_of_last_page = int(last_page.text.strip())
				#итерация по всем страницам
				for i in range(int(number_of_last_page)-1):
					url = f'{base_url}&page={i+2}' #первая страница соответствует базовому "base_url",а страницы с "page=0" не существует, поэтому отсчет начинается с "page=2"
					if url not in urls:
						urls.append(url)
		except Exception as e:
			print(f'{datetime.datetime.now()} Pagination Error:', e)

		#итерация по всем страницам
		for url in urls:
			data = get_page_data(url)
			ads.extend(data)
	else:
		print('Error')
	end = datetime.datetime.now()
	print(f'Время выполнения парсинга: {round((end - start).total_seconds(), 2)} с')
	return ads


if __name__ == '__main__':
	url = 'https://www.olx.ua/dom-i-sad/mebel/kiev/q-диван/?search%5Bfilter_float_price%3Afrom%5D=50&search%5Bfilter_float_price%3Ato%5D=4000&search%5Bfilter_enum_state%5D%5B0%5D=used&search%5Bdist%5D=50'
	data = olx_parse(url, headers)
	if data:
		print(len(data), data[0])
