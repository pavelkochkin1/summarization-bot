from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3 as sql
import asyncio
import datetime
from model import Model


class Choise(StatesGroup):
    text = State()
    xyu = State()


con = sql.connect('base.db')
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS base (
            id INTEGER,
            tgid INTEGER,
            text STRING,
            summary STRING,
            datetime STRING
            )""")
con.commit()


priv = 'Привет'


keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
summary = types.KeyboardButton('Сделать Summary')
history = types.KeyboardButton('История')
keyboard.add(summary, history)


def keyboard_history(ids):
    keyboard = types.InlineKeyboardMarkup()
    i = 1
    timeless = []
    for id in ids[::-1]:
        item = get_summary_by_id(id)
        if item:
            timeless.append(types.InlineKeyboardButton(text=item, callback_data=f'summary_{id[0]}'))
            if i % 2 == 0:
                keyboard.add(timeless[0], timeless[1])
                timeless = []
            i += 1
    if i % 2 == 0:
        keyboard.add(timeless[0])
    return keyboard


storage = MemoryStorage()
bot = Bot('2115628273:AAEXuw-3Mwtfd5ppK-uHwuutGv1ioxZW-_o')
dp = Dispatcher(bot, storage=storage)


def get_summary_by_id(id):
    id = id[0]
    cur.execute("SELECT summary FROM base WHERE id == ?", (id,))
    sum = cur.fetchone()
    if sum is not None:
        return sum[0]
    else:
        return False


def add_summary(userid, text, summary):
    dt = int(datetime.datetime.now().timestamp())
    cur.execute("SELECT id FROM base")
    id = cur.fetchall()
    if len(id) > 0:
        id = id[-1][0] + 1
    else:
        id = 1
    cur.execute("INSERT INTO base VALUES (?, ?, ?, ?, ?)", (id, userid, text, summary, dt))
    con.commit()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await bot.send_message(message.from_user.id, priv, reply_markup=keyboard)


@dp.message_handler(state=Choise.text)
async def txt(message: types.Message, state: FSMContext):
    answer = f"""{message.text}"""
    cur.execute("SELECT summary FROM base WHERE text == ?", (answer,))
    res = cur.fetchone()
    if res is not None:
        await bot.send_message(message.from_user.id, 'Мы нашли схожий текст. Вот готовое Summary:')
        await bot.send_message(message.from_user.id, res[0])
    else:
        await bot.send_message(message.from_user.id, 'Ожидайте...')
        summary = model.summarize(answer)
        await bot.delete_message(message.chat.id, message.message_id+1)
        await bot.send_message(message.from_user.id, summary)
        add_summary(message.from_user.id, answer, summary)
    await state.finish()


@dp.message_handler(content_types=['text'])
async def text(message: types.Message):
    if message.text == 'Сделать Summary':
        await bot.send_message(message.from_user.id, 'Введите текст для обработки:')
        await Choise.text.set()
    elif message.text == 'История':
        cur.execute('SELECT summary FROM base WHERE tgid == ?', (message.from_user.id,))
        summaries = cur.fetchall()
        if len(summaries) > 0:
            cur.execute('SELECT id FROM base WHERE tgid == ?', (message.from_user.id,))
            ids = cur.fetchall()
            await bot.send_message(message.from_user.id,
                                   'Ваши последние Summary:',
                                   reply_markup=keyboard_history(ids))
        else:
            await bot.send_message(message.from_user.id, 'У вас ещё нет сделанных Summary.', reply_markup=keyboard)


@dp.callback_query_handler(state='*')
async def callback_worker(call: types.CallbackQuery, state: FSMContext):
    data = call.data
    if 'summary' in data:
        sum_id = data.split('_')[1]
        cur.execute("SELECT summary FROM base WHERE id == ?", (sum_id,))
        summary = cur.fetchone()[0]
        cur.execute("SELECT datetime FROM base WHERE id == ?", (sum_id,))
        dt = datetime.datetime.fromtimestamp(cur.fetchone()[0])
        dt = datetime.datetime.strftime(dt, "%d.%m.%Y (%H:%M)")
        await bot.send_message(call.message.chat.id,
                               f'Ваше Summary за <b>{dt}</b>:\n\n{summary}',
                               parse_mode=types.ParseMode.HTML)


if __name__ == '__main__':
    model = Model()
    executor.start_polling(dp, skip_updates=True)
