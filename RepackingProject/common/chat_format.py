from __future__ import annotations

import logging
from lxml import etree


class Message:
    def __init__(self, author, text):
        self.author = author
        self.text = text


class MessageListContainer:
    def __init__(self, meeting_name, participants, meeting_datetime):
        self._messages = []
        self._meeting_name = meeting_name
        self._participants = participants
        self._meeting_datetime = meeting_datetime

    def add_message(self, message: Message):
        self._messages.append(message)

    def to_text(self) -> str:
        messages = "\n".join([f"\t{message.author}: {message.text}" for message in self._messages])
        text = \
f"""Количество участников: {self._participants},
Наименование команты: {self._meeting_name},
Дата и время: {self._meeting_datetime},
Сообщения:
{messages}
"""
        return text


def save_file(path, text: str):
    logging.info(f"Saving file: {path}")
    with open(path, 'w') as f:
        f.write(text)


def read_xml_popcorn(filename: str, message_list_container: MessageListContainer):
    """
    Считывает данные чата из xml и записывает в контейнер
    :param message_list_container:
    :param filename:
    """

    try:
        logging.info("Read xml popcorn")
        tree = etree.parse(filename)
        root = tree.getroot()

        for item in root:
            message = Message(author=item.get('name'), text=item.get('message'))
            message_list_container.add_message(message)
    except etree.XMLSyntaxError:
        logging.error("Syntax error xml popcorn")
        return None


def main():
    path = "../popcorn.xml"
    path_save = "../popcorn.txt"

    meeting_name = "SDM-2023"
    message_list_container = MessageListContainer(
        meeting_name,
        43,
        "2023-03-12T12:04:12"
    )
    read_xml_popcorn(path, message_list_container)
    save_file(path_save, message_list_container.to_text())


if __name__ == '__main__':
    main()
