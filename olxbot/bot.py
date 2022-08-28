from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

from config import BOT_TOKEN, RECIEVER_ID, TIME_PERIOD
from keyboards import *

from db import Database
import asyncio


class Filters_Info(StatesGroup):
	List = State()
	Info = State()

class Filters_Edit(StatesGroup):
	Title = State()
	Link = State()
	Delete = State()

class Filters_Create(StatesGroup):
	Title = State()
	Link = State()


bot = Bot(token=BOT_TOKEN)
loop = asyncio.get_event_loop()
dp = Dispatcher(bot, storage=MemoryStorage())
database = Database()
latest_upd = datetime.fromtimestamp(0)

def admin(func):
	async def wrapper(message):
		if message.from_user.id != int(RECIEVER_ID):
			return
		return await func(message)
	return wrapper

@dp.message_handler(commands=['start'], state='*')
async def process_start_command(msg: types.Message, state: FSMContext):
	await msg.reply(msg.from_user.id, reply=False)

@dp.message_handler(commands=['admin'], state='*')
@admin
async def enter_admin_panel(msg: types.Message):
	await msg.reply('OLX-bot адмін 😎', reply=False, reply_markup=admin_kb)


@dp.message_handler(lambda msg: msg.text[:-1].lower() == 'створення фільтрів', state='*')
async def new_filter_set_title(msg: types.Message, state: FSMContext):
	await Filters_Create.Title.set()
	await msg.reply('Введіть назву фільтру', reply=False, reply_markup=create_filter_kb)

@dp.message_handler(state=Filters_Create.Title)
async def new_filter_set_link(msg: types.Message, state: FSMContext):
	await Filters_Create.Link.set()
	await state.update_data(title=msg.text)
	await msg.reply('Введіть посилання для фільтру', reply=False, reply_markup=create_filter_kb)

@dp.message_handler(state=Filters_Create.Link)
async def new_filter_create(msg: types.Message, state: FSMContext):
	data = await state.get_data()
	title = data.get('title')
	url = msg.text
	database.create_filter(title, url)
	await msg.reply(f'Фильтр {title} створен!', reply=False)
	await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'cancel_creat', state=[Filters_Create.Title, Filters_Create.Link])
async def new_filter_cancel(callback_query: types.CallbackQuery, state: FSMContext):
	await bot.send_message(callback_query.from_user.id, 'Створення фільтру скасовано!')
	await state.finish()

@dp.message_handler(lambda msg: msg.text[:-2].lower() == 'редагування фільтрів', state='*')
async def filters_list(msg: types.Message, state: FSMContext):
	filters = database.get_all_filters()
	await msg.reply(
		f'Всего фильтрів у базі: {len(filters)}.\n\nВиберіть фильтр, щоб перейти до його редагування.',
		reply=False,
		reply_markup=filters_list_kb(filters)
	)
	await Filters_Info.List.set()
	await state.update_data(filters=filters, page=0)

@dp.callback_query_handler(lambda c: c.data == 'quit_filters', state=Filters_Info.List)
async def filter_list_quit(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.message.delete()
	await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'next' or c.data == 'prev', state=Filters_Info.List)
async def filters_list_change_page(callback_query: types.CallbackQuery, state: FSMContext):
	data = await state.get_data()
	filters = data.get('filters')
	delta = 1
	if callback_query.data == 'prev':
		delta = -1 
	page = data.get('page') + delta
	await callback_query.message.edit_reply_markup(filters_list_kb(filters, page=page))
	await state.update_data(page=page)

async def send_filter_info(filter_id, uid):
	filter = database.get_filter(filter_id)
	await bot.send_message(uid, f'Назва: <b>{filter[1]}</b>\n\nПосилання: {filter[2]}', reply_markup=edit_filter_kb, parse_mode=types.ParseMode.HTML)

@dp.callback_query_handler(lambda c: c.data[:3] == '[f]', state=Filters_Info.List)
async def filter_control(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.message.delete()
	filter_id = int(callback_query.data[3:])
	await send_filter_info(filter_id, callback_query.from_user.id)
	await Filters_Info.Info.set()
	await state.update_data(filter_id=filter_id)

@dp.callback_query_handler(lambda c: c.data == 'title', state=Filters_Info.Info)
async def filter_edit_title(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.message.delete()
	await bot.send_message(callback_query.from_user.id, 'Введіть нову назву фільтру', reply_markup=edit_filter_param_kb)
	await Filters_Edit.Title.set()

@dp.callback_query_handler(lambda c: c.data == 'url', state=Filters_Info.Info)
async def filter_edit_link(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.message.delete()
	await bot.send_message(callback_query.from_user.id, 'Введіть нове посилання фільтру', reply_markup=edit_filter_param_kb)
	await Filters_Edit.Link.set()

@dp.callback_query_handler(lambda c: c.data == 'delete', state=Filters_Info.Info)
async def filter_confirm_deletion(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.message.delete()
	await bot.send_message(callback_query.from_user.id, 'Видалити фильтр?', reply_markup=confirmation_kb)
	await Filters_Edit.Delete.set()

@dp.callback_query_handler(lambda c: c.data == 'to_list', state=Filters_Info.Info)
async def backto_filter_list(callback_query: types.CallbackQuery, state: FSMContext):
	data = await state.get_data()
	page = data.get('page', 0)
	filters = database.get_all_filters()
	await bot.send_message(
		callback_query.from_user.id,
		f'Всего фильтрів у базі: {len(filters)}.\n\nВиберіть фильтр, щоб перейти до його редагування.',
		reply_markup=filters_list_kb(filters, page=page)
	)
	await callback_query.message.delete()
	await Filters_Info.List.set()

@dp.callback_query_handler(lambda c: c.data == 'to_control', state=[Filters_Edit.Title, Filters_Edit.Link])
async def backto_filter_control(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.message.delete()
	data = await state.get_data()
	filter_id = data.get('filter_id')
	await send_filter_info(filter_id, callback_query.from_user.id)
	await Filters_Info.Info.set()

@dp.callback_query_handler(state=Filters_Edit.Delete)
async def filter_delete(callback_query: types.CallbackQuery, state: FSMContext):
	data = await state.get_data()
	filter_id = data.get('filter_id')
	if callback_query.data == 'y':
		await callback_query.message.delete()
		database.delete_filter(filter_id)
		await bot.send_message(callback_query.from_user.id, 'Фильтр видалено!')
		await state.finish()
	elif callback_query.data == 'n':
		await callback_query.message.delete()
		await send_filter_info(filter_id, callback_query.from_user.id)
		await Filters_Info.Info.set()
	else:
		return

@dp.message_handler(state=Filters_Edit.Title)
async def filter_update_title(msg: types.Message, state: FSMContext):
	data = await state.get_data()
	filter_id = data.get('filter_id')
	database.update_filter_title(filter_id, msg.text)
	await send_filter_info(filter_id, msg.from_user.id)
	await Filters_Info.Info.set()

@dp.message_handler(state=Filters_Edit.Link)
async def filter_update_link(msg: types.Message, state: FSMContext):
	data = await state.get_data()
	filter_id = data.get('filter_id')
	database.update_filter_link(filter_id, msg.text)
	await send_filter_info(filter_id, msg.from_user.id)
	await Filters_Info.Info.set()


if __name__ == '__main__':
	scheduler = AsyncIOScheduler(timezone='Europe/Kiev')
	scheduler.add_job(parse_olx, 'interval', seconds=TIME_PERIOD)
	scheduler.start()
	executor.start_polling(dp)



