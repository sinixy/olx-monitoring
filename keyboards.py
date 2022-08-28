from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton


def filters_list_kb(filters_list, page=0, count=3):
	res = InlineKeyboardMarkup()
	start = page * count
	end = start + count
	filters = filters_list[start:end]
	for f in filters:
		id = f[0]
		title = f[1]
		res.add(InlineKeyboardButton(title, callback_data='[f]' + str(id)))
	if len(filters_list) > count:
		control_buttons = []
		if page > 0:
			control_buttons.append(InlineKeyboardButton('⬅️', callback_data='prev'))
		if end < len(filters_list):
			control_buttons.append(InlineKeyboardButton('➡️', callback_data='next'))
		res.row(*control_buttons)
	res.add(InlineKeyboardButton('Выйти', callback_data='quit_filters'))
	return res


admin_kb = ReplyKeyboardMarkup(keyboard=
	[
		[KeyboardButton('Создание фильтров➕')],
		[KeyboardButton('Редактирование фильтров✏️')]

	]
)

edit_filter_kb = InlineKeyboardMarkup()
edit_filter_kb.add(InlineKeyboardButton('Поменять название', callback_data='title'))
edit_filter_kb.add(InlineKeyboardButton('Поменять ссылку', callback_data='url'))
edit_filter_kb.add(InlineKeyboardButton('Удалить', callback_data='delete'))
edit_filter_kb.add(InlineKeyboardButton('Назад', callback_data='to_list'))

edit_filter_param_kb = InlineKeyboardMarkup()
edit_filter_param_kb.add(InlineKeyboardButton('Отмена', callback_data='to_control'))

create_filter_kb = InlineKeyboardMarkup()
create_filter_kb.add(InlineKeyboardButton('Отмена', callback_data='cancel_creat'))

confirmation_kb = InlineKeyboardMarkup()
confirmation_kb.row(
	InlineKeyboardButton('Да', callback_data='y'),
	InlineKeyboardButton('Нет', callback_data='n')
)