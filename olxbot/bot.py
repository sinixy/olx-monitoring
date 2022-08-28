from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bson.objectid import ObjectId

from config import BOT_TOKEN, RECIEVER_ID
from .db import db
from .keyboards import *
from .olx import get_query_params


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
dp = Dispatcher(bot, storage=MemoryStorage())


def admin(func):
    async def wrapper(message):
        if message.from_user.id != int(RECIEVER_ID):
            return
        return await func(message)
    return wrapper

async def send_filter_info(filter_id, uid):
    filter = await db.filters.find_one({'_id': ObjectId(filter_id)})
    await bot.send_message(
        uid,
        f'Назва: <b>{filter["title"]}</b>\n\nПосилання: {filter["url"]}',
        reply_markup=edit_filter_kb,
        parse_mode=types.ParseMode.HTML
    )


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
    query_params = await get_query_params(url)
    if query_params:
        await db.filters.insert_one({'title': title, 'url': url, 'params': query_params})
        await msg.reply(f'Фильтр {title} створено!', reply=False)
        await state.finish()
    else:
        await msg.reply('⚠️ Не можу визначити параметри фільтру! Перевірте коректність посилання.', reply=False)
        await msg.reply('Введіть посилання для фільтру', reply=False, reply_markup=create_filter_kb)

@dp.callback_query_handler(lambda c: c.data == 'cancel_creat', state=[Filters_Create.Title, Filters_Create.Link])
async def new_filter_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, 'Створення фільтру скасовано!')
    await state.finish()

@dp.message_handler(lambda msg: msg.text[:-2].lower() == 'редагування фільтрів', state='*')
async def filters_list(msg: types.Message, state: FSMContext):
    filters = await db.filters.find({}).to_list(None)
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

@dp.callback_query_handler(lambda c: c.data[:3] == '[f]', state=Filters_Info.List)
async def filter_control(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    filter_id = callback_query.data[3:]
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
    filters = await db.filters.find({}).to_list(None)
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
        await db.filters.delete_one({'_id': ObjectId(filter_id)})
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
    await db.filters.update_one({'_id': ObjectId(filter_id)}, {'$set': {'title': msg.text}})
    await send_filter_info(filter_id, msg.from_user.id)
    await Filters_Info.Info.set()

@dp.message_handler(state=Filters_Edit.Link)
async def filter_update_link(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    filter_id = data.get('filter_id')
    url = msg.text
    query_params = await get_query_params(url)
    if query_params:
        await db.filters.update_one({'_id': ObjectId(filter_id)}, {'$set': {'url': url, 'params': query_params}})
        await send_filter_info(filter_id, msg.from_user.id)
        await Filters_Info.Info.set()
    else:
        await msg.reply('⚠️ Не можу визначити параметри фільтру! Перевірте коректність посилання.', reply=False)
        await msg.reply('Введіть нове посилання фільтру', reply=False, reply_markup=edit_filter_param_kb)
    
    

