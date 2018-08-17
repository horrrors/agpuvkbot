import requests


class Vk_api:
    """Класс, обеспечивающий инкапсуляцию апи методов сервиса Вконтакте"""

    def __init__(self):
        # token agpu bot
        self.token = ('71c6b0f01987e3a7972aecb1d9ef83a95a3791513'
                      'ce19cb825ec487fb15f7d063a375b71f56ea6731d35c')
        self.v = '5.80'
        self.params = {'access_token': self.token, 'v': self.v}

    def method(self, name, kwargs):
        """Обобщенный метод для работы с различными апи вк"""
        kwargs.update(self.params)
        return requests.get('https://api.vk.com/method/{}'.format(name),
                            params=kwargs).json()

    def send(self, *args, **kwargs):
        """
        (User_id, message, attachment, keyboard)
        Обертка отправки сообщения над обобщенным методом"""
        self.method('messages.send', kwargs)

    def attach(self, pic):
        """Получает сервер для загрузки, загружает фотографию
        конструирует и возвращает строку attachement"""
        url = self.method('photos.getMessagesUploadServer', self.params)
        pic = open(''.join(pic), 'rb')
        upload = requests.post(url['response']['upload_url'],
                               files={'photo': pic}).json()
        ph_dict = {'photo': upload['photo'],
                   'server': upload['server'],
                   'hash': upload['hash']}
        uploaded = self.method('photos.saveMessagesPhoto', ph_dict)
        return 'photo{}_{}'.format(uploaded['response'][0]['owner_id'],
                                   uploaded['response'][0]['id'])

    def last_messages(self):
        """Возвращает список состоящий из сообщений и id их владельцев"""
        convs = self.method('messages.getConversations', {'count': 10,
                                                          'filter': 'unread'})
        lst = []
        for conv in convs['response']['items']:
            dick = {'user_id': conv['conversation']['peer']['id'],
                    'offset': -10,
                    'count': 10,
                    'start_message_id': -1}
            for mes in self.method('messages.getHistory',
                                   dick)['response']['items']:
                lst.append((mes['from_id'], mes['text'].capitalize()))
        return lst

    def getUser(self, id):
        """Обертка апи метода по получению данных о конкретном человеке"""
        return self.method('users.get',
                           {'user_ids': id})['response'][0]['first_name']


if __name__ == '__main__':
    pass
