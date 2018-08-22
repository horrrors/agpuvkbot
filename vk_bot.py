#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==============
from config import *
from vk_api import Vk_api
import random
import time
import json
from datetime import datetime, date
from datetime import timedelta
import copy
import traceback
from requests.packages.urllib3.exceptions import ProtocolError


class Bot:
    """Класс, который выполняет
     основную логику чат бота, используя класс вк апи"""

    # Конструктор класса
    def __init__(self):
        self.vk = Vk_api()
        self.url = ('http://www.it-institut.ru'
                    '/Raspisanie/SearchedRaspisanie?OwnerId=118&SearchId='
                    '{}&SearchString={}&Type={}&WeekId={}')
        self.keyboard = {}

    def execute(self, str, arg=None, type=None):
        """Инкапсулирует работу с базой данных"""
        cur = con.cursor()

        cur.execute(str, arg) if arg else cur.execute(str)

        if str.startswith('INSERT') or str.startswith('UPDATE'):
            con.commit()
            return

        return cur.fetchall() if type else cur.fetchone()

    def get_cur_date(self):
        """Получение значения текущей недели,
           а так же обновление его при необходимости"""
        data, number = self.execute("SELECT bddata,number FROM dates "
                                    "WHERE name='bddatanow'")
        delta = datetime.now().date() - data
        if delta.days >= 7:
            data = data + timedelta(days=7)
            number += 1
            self.execute("UPDATE dates SET number=(%s),bddata=(%s) "
                         "WHERE name='bddatanow'", (number, data))
        return int(number)

    def driver_get_screen(self, url):
        """Обертка над драйвером получения
        скриншота с примененными настройками"""
        driver.get(url)
        driver.set_window_size(1540, 1150)
        driver.execute_script("window.scrollTo(330, 525)")
        driver.get_screenshot_as_file(path)

    def makescreen(self, group, id, type):
        """Конструирует скриншот исходя из поданных на вход данных
        записыват скриншот в виде бинарника в базу к группе, к которой
        он относится"""
        self.driver_get_screen(self.url.format(id, group, type,
                                               str(self.get_cur_date())))
        self.execute("UPDATE bytes SET byte=(%s) WHERE name=(%s)",
                     (psycopg2.Binary(open('group.png', 'rb').read()),
                      group))

    def is_reg(self, id):
        """Проверка пользователя на регистрацию"""
        return True if self.execute("SELECT id from rassilka where id=%s",
                                    (str(id),)) else False

    def is_dispatch(self, id):
        """Проверка пользователя на рассылку"""
        return eval(self.execute("SELECT dispatch from rassilka where id=(%s)",
                                 (id,))[-1])

    def is_changes(self, id):
        """Проверка пользователя """
        return eval(self.execute("SELECT changes from rassilka where id=(%s)",
                                 (id,))[-1])

    def make_keyboard(self, id, suggest=None):
        """Конструирует клавиатуру исходя из проверок,
           так же добавляет предложенные варианты"""
        self.keyboard = copy.deepcopy(keyboard)

        if self.is_reg(id):
            self.keyboard['buttons'].append(dbut['get_rasp'])
            if suggest:
                for sug in suggest[:6]:
                    self.button = copy.deepcopy(button)
                    self.button['action']['label'] = sug
                    self.keyboard['buttons'].append([self.button])
            else:
                self.keyboard['buttons'].append(dbut['get_rasp_next'])
                self.keyboard['buttons'].append(dbut['get_rasp_prev'])
                if self.is_dispatch(id):
                    self.keyboard['buttons'].append(dbut['dispatch_false'])
                else:
                    self.keyboard['buttons'].append(dbut['dispatch_true'])
                if self.is_changes(id):
                    self.keyboard['buttons'].append(dbut['changes_false'])
                else:
                    self.keyboard['buttons'].append(dbut['changes_true'])

        return str(json.dumps(self.keyboard, ensure_ascii=False))

    def getsend(self, id, message):
        """Делает скриншоты в realtime
           Отвечает за отправку скриншотов следующих недель,
           так же отвечает за команду обновления"""
        try:
            message = message.replace('обновить', '').rstrip()

            if message.find('+') != -1:
                split = message.split('+')
                message = split[0].rstrip()
                data += int(split[1])

            username = self.vk.getUser(id)
            group, grpid, type = self.execute("SELECT * FROM ids "
                                              "WHERE name=%s",
                                              (message,))
            self.driver_get_screen(self.url.format(id, grpid, type,
                                                   str(data)))
            self.vk.send(user_id=id,
                         message=random.choice(complete).format(username),
                         attachment=self.vk.attach('group.png'),
                         keyboard=self.make_keyboard(id))
        except Exception:
            self.make_error(id, message)

    def make_error(self, id, message):
        """Пытается искать совпадения и выдает найденные предложения"""
        source = self.execute("SELECT name from ids WHERE name like %s",
                              ('%{}%'.format(message),), 'fetchall')
        suggest = [x[0] for x in source[:10]]
        self.vk.send(user_id=id, message=random.choice(sorry),
                     keyboard=self.make_keyboard(id, suggest))

    def sendfrombytes(self, id, message):
        """Восстанавливает из бинарника скриншот и отправляет его"""
        try:
            source = self.execute("SELECT * from bytes WHERE name=%s",
                                  (message,))
            open('bytepic.png', 'wb').write(source[1])
            username = self.vk.getUser(id)
            self.vk.send(user_id=id,
                         message=random.choice(complete).format(username),
                         attachment=self.vk.attach('bytepic.png'),
                         keyboard=self.make_keyboard(id))

        except Exception:
            self.getsend(id, message)

    def screeneveryday(self):
        """Сверяет дату и при необходимости переводит число
           и обновляет скриншоты"""
        data = self.execute("SELECT bddata from dates where"
                            " name=%s", ('bddataeveryday',))[0]

        delta = datetime.now().date() - data

        if delta.days >= 1:
            data = data + timedelta(days=1)
            self.execute("UPDATE dates set bddata=(%s) WHERE name=(%s)",
                         (data, 'bddataeveryday'))

            for row in self.execute("SELECT * FROM ids", type='fetchall'):
                self.makescreen(*row)

    def send_rassilka(self):
        """Отправляет каждую субботу рассылку"""
        data = self.execute("SELECT bddata FROM dates WHERE name=%s",
                            ('bddatarassilka',))[-1]
        delta = datetime.now().date() - data

        if delta.days >= 7:
            data = data + timedelta(days=7)
            self.execute("UPDATE dates SET bddata=(%s) WHERE name=(%s)",
                         (data, 'bddatarassilka'))

            for row in self.execute("SELECT id, grupa FROM rassilka "
                                    "WHERE dispatch='True'", type='fetchall'):
                self.getsend(*row)

    def get_rasp(self, id):
        """Обработка кнопки мое расписание"""
        self.execute("SELECT grupa from rassilka where id=%s", (id,))
        message = self.execute("SELECT grupa from rassilka where id=%s",
                               (id,))[-1]
        self.sendfrombytes(id, message)

    def get_prev_next(self, id, message):
        """Обработка кнопок следующая и предыдущая"""
        if message.find('следующая') != -1:
            data = self.get_cur_date() + 1
        else:
            data = self.get_cur_date() - 1

        message = self.execute("SELECT grupa from rassilka where id=%s",
                               (id,))[-1]

        username = self.vk.getUser(id)
        group, grpid, type = self.execute("SELECT * FROM ids WHERE name=%s",
                                          (message,))
        self.driver_get_screen(self.url.format(id, grpid, type, str(data)))
        self.vk.send(user_id=id,
                     message=random.choice(complete).format(username),
                     attachment=self.vk.attach('group.png'),
                     keyboard=self.make_keyboard(id))

    def get_registration(self, id, message):
        """Производит регистрацию пользователя в базе"""
        message = message.split()[-1].capitalize()
        self.execute("INSERT INTO rassilka(id, grupa) VALUES(%s,%s)",
                     (str(id), message))
        self.vk.send(user_id=id, message=reg,
                     keyboard=self.make_keyboard(id))

    def get_dispatch(self, id):
        """Отвечает за обработку кнопки подключение рассылки"""
        self.execute("UPDATE rassilka set dispatch='True' WHERE id=%s", (id,))
        self.vk.send(user_id=id, message=regdisp,
                     keyboard=self.make_keyboard(id))

    def unget_dispatch(self, id):
        """Отвечает за обработку кнопки отключения рассылки"""
        self.execute("UPDATE rassilka set dispatch='False' WHERE id=%s", (id,))
        self.vk.send(user_id=id, message=unregdisp,
                     keyboard=self.make_keyboard(id))

    def get_changes(self, id):
        """Отвечает за кнопку подключения изменений"""
        self.execute("UPDATE rassilka set changes='True' WHERE id=%s", (id,))
        self.vk.send(user_id=id, message=regchanges,
                     keyboard=self.make_keyboard(id))

    def unget_changes(self, id):
        """Отвечает за кноку отключения изменений"""
        cur = con.cursor()
        cur.execute("UPDATE rassilka set changes='False' WHERE id=%s", (id,))
        self.vk.send(user_id=id, message=unregchanges,
                     keyboard=self.make_keyboard(id))

    def choose_way(self, id, message):
        """Направление первичного сообщения в нужный путь обработки"""
        if message.find('Регистрация') != -1:
            self.get_registration(id, message)

        elif message.find('обновить') != -1:
            self.getsend(id, message)

        elif message == 'Подписаться на рассылку':
            self.get_dispatch(id)

        elif message == 'Отписаться от рассылки':
            self.unget_dispatch(id)

        elif message == 'Подписаться на изменения':
            self.get_changes(id)

        elif message == 'Отписаться от изменений':
            self.unget_changes(id)

        elif message == 'Мое расписание':
            self.get_rasp(id)

        elif message.find('Моя') != -1:
            self.get_prev_next(id, message)

        else:
            self.sendfrombytes(id, message)

    def run(self):
        """Вечный цикл бота"""
        while True:
            try:
                self.screeneveryday()
                self.send_rassilka()
                for id, message in self.vk.last_messages():
                    self.choose_way(str(id), str(message))
                    time.sleep(1)

            except:
                traceback.print_exc()
                time.sleep(5)


if __name__ == '__main__':
    bot = Bot()
    bot.run()
