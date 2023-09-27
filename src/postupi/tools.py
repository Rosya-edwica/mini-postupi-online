import re

import aiohttp
from bs4 import BeautifulSoup
from bs4.element import Tag
from lxml import etree

from models import ProgramHeader, ProgramDetails


async def GetHTML(url: str, headers: dict = None) -> BeautifulSoup:
    """Метод для асинхронных request-запросов"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return BeautifulSoup(await response.text(), "lxml")


def UniqueListItems(data: list) -> list:
        """Оставляем только уникальные элементы в списке"""
        unique = []
        for i in data:
            if i not in unique:
                unique.append(i)
        return unique


def GetProgramSubjects(html: Tag) -> list[str]:
    """Получаем список предметов ЕГЭ для бакалавров и специалистов и список экзаменов для магистров"""
    ege_subjects =  html.find("div", class_="score-box swiper-slide 0")
    if ege_subjects:
            return [re.sub(r"\xa0|другие", " ", subject.text).replace("или ", "/").replace("/ ", "")
                        for subject in ege_subjects.find_all("div", class_="score-box__item")]

    # Для магистров
    exams = html.find_all("div", class_="score-box__inner")
    subjects = []
    for item in exams:
        for exam in item.find_all("div", class_="score-box__item"):
                subjects.append(exam.text)
    return subjects


def GetProgramDetails(html: Tag) -> ProgramDetails:
    """Собираем уровень образования и форму обучения из блока Детали"""
    section_items = html.find_all("div", class_="detail-box__item")
    for item in section_items:
        text = item.text.strip().replace("\n", "")
        if "Уровень образования" in text:
            level = re.sub("Уровень образования", "", text)
        elif "Форма обучения" in text:
            form = re.sub("Форма обучения|\xa0|\n", "", text)
    return ProgramDetails(level, form)


def GetProgramHeader(html: Tag, url) -> ProgramHeader:
    """Собираем стоимость обучения, количество платных и бюджетных мест, продолжительность обучения в месяцах"""
    cost, free_places, payment_places, duration_in_months = 0, 0, 0, 0
    header_items = html.find("ul", class_="bg-nd__cnt bg-nd-cnt swiper-wrapper").find_all("li")

    for item in header_items:
        dom = etree.HTML(str(item))
        block_title = dom.xpath("//span[contains(@class, 'bg-nd-cnt__txt')]")[0].text.strip()
        block_num = item.find("span", class_="bg-nd-cnt__num")
        if block_num is None: 
            continue
        else:
            block_num = block_num.text.replace(u"\xa0", u"")
        match block_title:
            case "рублей в год":
                cost = re.findall("\d+", block_num)[0]
            case "бюджет.":
                free_places = int(block_num)
            case "платных" | "платное":
                payment_places = int(block_num)
            case "обучения":
                duration_in_months = DurationToMonths(block_num)
            case _:
                print(f"НЕ ПОЛУЧИЛОСЬ ОБРАБОТАТЬ ЗАГОЛОВОК ПРОГРАММЫ: ({block_title}) {url}")

    return ProgramHeader(cost, free_places, payment_places, duration_in_months)


def DurationToMonths(text: str) -> int:
    """Конвертируем это '3 года и 3 мес.' в это '39'(месяцев)"""
    months = 0
    years = re.findall("\d+ год|\d+ лет", text)
    if years:
        months += int(re.findall("\d+", years[0])[0]) * 12

    months_block = re.findall("\d+ мес", text)
    if months_block:
        months += int(re.findall("\d+", months_block[0])[0])
    return months