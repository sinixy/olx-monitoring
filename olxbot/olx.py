import asyncio
import aiohttp
from aiohttp.client_exceptions import ClientOSError, ClientPayloadError
from aiogram import types
from datetime import datetime
from pymongo import InsertOne
from .utils import prettify_duration
from .keyboards import offer_kb
from config import OFFER_RAW_FIELDS, RECIEVER_ID

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36 OPR/60.0.3255.170",
    "accept": "*/*"
}


async def get_query_params(filter_url):
    url = 'https://www.olx.ua/api/v1/friendly-links/query-params/'
    general = []
    for u in filter_url.split('/'):
        if u.lower() in ['https:', '', 'www.olx.ua', 'd', 'uk']:
            continue
        if u[0] == '?':
            url += ','.join(general) + '/' + u
            break
        else:
            general.append(u)
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                result = await resp.json()
                if query_params := result.get('data'):
                    return query_params

async def get_offers(url=None, **params):
    session = aiohttp.ClientSession(headers=headers)
    response = {}

    if url:
        async with session.get(url) as resp:
            if resp.status == 200:
                response = await resp.json()
    else:
        if 'limit' not in params.keys():
            params['limit'] = 50
        if 'offset' not in params.keys():
            params['offset'] = 0
        if 'sort_by' not in params.keys():
            params['sort_by'] = 'created_at:desc'
        async with session.get('https://www.olx.ua/api/v1/offers/', params=params) as resp:
            if resp.status == 200:
                response = await resp.json()

    await session.close()
    return response

def get_filtered_offers(new_offers, old_offers_id, filter_name):
        res = []
        for o in new_offers:
            if o['id'] in old_offers_id:
                continue
            t = datetime.fromisoformat(o['created_time'].split('+')[0])
            today = datetime.today()
            if t.year != today.year or t.month != today.month or t.day != today.day:
                continue
            tmp = {}
            for k, v in o.items():
                if k not in OFFER_RAW_FIELDS:
                    continue
                if k == 'id':
                    tmp['_id'] = v
                elif k == 'created_time':
                    tmp['created_time'] = t
                elif k == 'params':
                    for param in v:
                        if param['key'] == 'price':
                            tmp['price'] = param['value']['label']
                elif k == 'photos':
                    tmp[k] = [photo['link'].split(';')[0] for photo in v]
                elif k == 'description':
                    description = v.replace('<br />', '')
                    if len(v) > 1024:
                        description = description[:1024] + '...'
                    tmp[k] = description
                else:
                    tmp[k] = v
            tmp['filter'] = filter_name
            res.append(tmp)
        return res

async def send_reports(offers, bot):
    for o in offers:
        report = ''
        icon = '❗️'
        if photos := o.get('photos'):
            preview_url = photos[0]
            icon = f'<a href="{preview_url}">{icon}</a>'
        report += icon + f' <b>{o["title"]}</b>\n\n'
        report += '⚙️ <b>Фільтр</b>: ' + o['filter'] + '\n'
        report += '💰 <b>Ціна</b>: ' + o['price'] + '\n'
        report += '⏳ <b>Створено</b>: ' + prettify_duration(datetime.now() - o['created_time']) + ' тому\n'
        report += '✏️ <b>Опис</b>: ' + o['description']
        await bot.send_message(
            RECIEVER_ID,
            report,
            parse_mode=types.ParseMode.HTML,
            reply_markup=offer_kb(o["url"])
        )

async def start_olx_polling(bot, db, loop):
    while True:
        start = datetime.now()
        filters = await db.filters.find({}).to_list(None)
        if not filters:
            print('Waiting for filters...')
            await asyncio.sleep(5)
            continue
        offers = [o['_id'] for o in await db.offers.find({}, projection=['_id']).to_list(None)]
        new_offers = []
        total_elements = []
        for f in filters:
            try:
                resp = await get_offers(**f['params'])
            except (ClientOSError, ClientPayloadError):
                await asyncio.sleep(10)
                break
            total_elements.append(resp.get('metadata', {}).get('total_elements', None))
            filtered_offers = get_filtered_offers(resp.get('data', []), offers, f['title'])
            if not filtered_offers:
                continue
            new_offers.extend(filtered_offers)
            offers.extend([fo['_id'] for fo in filtered_offers])

            next_page = resp.get('links', {}).get('next', {}).get('href')
            while next_page:
                try:
                    resp = await get_offers(next_page)
                except ClientOSError:
                    await asyncio.sleep(10)
                    break
                filtered_offers = get_filtered_offers(resp.get('data', []), offers, f['title'])
                if not filtered_offers:
                    break
                new_offers.extend(filtered_offers)
                offers.extend([fo['_id'] for fo in filtered_offers])
                next_page = resp.get('links', {}).get('next', {}).get('href')

        if new_offers:
            await db.offers.bulk_write([InsertOne(no) for no in new_offers])
            loop.create_task(send_reports(new_offers, bot))
        end = datetime.now()
        print('Cycle duration:', (end - start).total_seconds(), 's', total_elements)
    

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(start_olx_polling())
