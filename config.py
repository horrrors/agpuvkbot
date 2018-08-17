import os
import psycopg2
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'group.png')

# настройки вебдрайвера для скринов
options = webdriver.ChromeOptions()
options.binary_location = "/app/.apt/usr/bin/google-chrome-stable"
driver = webdriver.Chrome(chrome_options=options)

# подключение к базе heroku
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
con = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)


keyboard = {
    'one_time': True,
    'buttons': []
}

button = {'action': {'type': 'text'},
          'color': 'negative'}


dbut = {'dispatch_true': [{'action': {'type': 'text',
                                      'label': 'Подписаться на рассылку'},
                           'color': 'positive'}],
        'dispatch_false': [{'action': {'type': 'text',
                                       'label': 'Отписаться от рассылки'},
                            'color': 'negative'}],
        'changes_true': [{'action': {'type': 'text',
                                     'label': 'Подписаться на изменения'},
                          'color': 'positive'}],
        'changes_false': [{'action': {'type': 'text',
                                      'label': 'Отписаться от изменений'},
                           'color': 'negative'}],
        'get_rasp': [{'action': {'type': 'text',
                                 'label': 'Мое расписание'},
                      'color': 'primary'}],
        'get_rasp_next': [{'action': {'type': 'text',
                                      'label': 'Моя следующая неделя'},
                           'color': 'primary'}],
        'get_rasp_prev': [{'action': {'type': 'text',
                                      'label': 'Моя предыдущая неделя'},
                           'color': 'primary'}],
        }

# массив строк уведомлений об ошибках
sorry = ['Скорее всего вы ошиблись с названием своей'
         'группы или с преподавателем, '
         'проверьте правильность вводимых данных🌈 \n '
         'Однако вот, что мне удалось найти похожее: \n',
         'Что-то пошло не так!🍓 Возможно, вы где-то ошиблись, '
         'постараюсь вам помочь, вот, что у меня есть похожее:\n',
         'Где-то закралась ошибка! Возможно, '
         'я могу вам помочь и показать, с чем есть совпадения!🐥\n'
         ]


# массив строк об успешном получении
complete = ['{}, кажется, это то, что вам нужно!🌈',
            'Какое счастье, {}, мне удалось найти ваше расписание🌈',
            'Не это ли вы ищете, {}?🌈'
            ]

regdisp = '🌈Рассылка подключена🌈\n'
unregdisp = 'Рассылка отключена :('
regchanges = 'Вы подписались на изменения!'
unregchanges = 'Вы отписались от изменений :('
reg = 'Вы зарегистрированы!'

if __name__ == '__main__':
    pass
