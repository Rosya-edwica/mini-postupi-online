import re

import asyncio
from bs4.element import Tag

from postupi import *
from db import Database
from models import *


class PostupiOnline:
    def __init__(self, database: Database):
        self.MAIN_PAGE = "https://postupi.online/vuzi/"
        self.LEVEL_DOMAINS = ("bakalavr", "specialist", "magistratura")
        self.database = database
        self.current_vuz_abbr: str

    async def Run(self):
        pages_count = await self.get_pages_count(self.MAIN_PAGE)
        for page in range(1, pages_count+1):
            await self.ScrapePage(url=f"{self.MAIN_PAGE}?page_num={page}")

    async def ScrapePage(self, url: str):
        page_items = await self.get_page_items(url)
        for item in page_items:
            vuz_url = item.find("h2", class_="list__h").find("a")["href"]
            await self.ScrapeVuz(vuz_url)

    async def ScrapeVuz(self, url: str):
        html = await GetHTML(url)
        vuz = Vuz(
            Abbr=url.split("/")[-2],
            Name=html.find("h1").text,
            City=html.find("p", class_="bg-nd__pre").text
        )
        self.current_vuz_abbr = vuz.Abbr
        await self.database.SaveVuz(vuz)
        await self.ScrapeVuzSpecializations(url)
    

    async def ScrapeVuzSpecializations(self, vuz_url: str):
        for domain in self.LEVEL_DOMAINS:
            url = f"{vuz_url}/specialnosti/{domain}"
            pages_count = await self.get_pages_count(url)
            for page in range(1, pages_count+1):
                page_url = f"{url}?page_num={page}"
                await self.ScrapeSpecializations(page_url)


    async def ScrapeSpecializations(self, url: str):
        page_items = await self.get_page_items(url)
        specs = []
        for item in page_items:
            pre_title = item.find("p", class_="list__pre").text.strip()
            code = re.findall(r"\d+.\d+.\d+", pre_title)[0]

            spec = Specialization(
                VuzAbbr=self.current_vuz_abbr,
                Code=code,
                Name=item.find("h2").text,
                Direction=pre_title.replace(code, ""),
                Url=item.find("h2").find("a")["href"]
            )
            specs.append(spec)
        [await asyncio.create_task(self.database.SaveSpecialization(spec)) for spec in specs]
        [await asyncio.create_task(self.ScrapeSpecializationPrograms(spec.Url)) for spec in specs]
    
    async def ScrapeSpecializationPrograms(self, spec_url: str):
        program_items =  await self.get_page_items(spec_url)
        spec_code = spec_url.split("/")[-2]
        tasks = [asyncio.create_task(
            self.ScrapeProgram(url=item.find("h2").find("a")["href"], spec_code=spec_code)) 
            for item in program_items]
        programs = await asyncio.gather(*tasks)
        [await self.database.SaveProgram(program) for program in programs]


    async def ScrapeProgram(self, url: str, spec_code: str) -> Program:
        html = await GetHTML(url)
        header = GetProgramHeader(html, url)
        details = GetProgramDetails(html)
        program = Program(
            Url=url,
            SpecCode=spec_code,
            Cost=header.Cost,
            Form=details.Form,
            Level=details.Level,
            FreePlaces=header.FreePlaces,
            VuzAbbr=self.current_vuz_abbr,
            PaymentPlaces=header.PaymentPlaces,
            DurationInMonths=header.DurationInMonths,
            Name=html.find("h1").text.split(":")[0],
            IsPayment=True if header.PaymentPlaces > 0 else False,
            Subjects=UniqueListItems(GetProgramSubjects(html)),
        )
        return program    
    
    async def get_pages_count(self, url: str) -> int:
        html = await GetHTML(url)
        try:
            return int(html.find_all("a", class_="paginator")[-1].text)
        except IndexError:
            return 1
    
    async def get_page_items(self, url: str) -> list[Tag]:
        html = await GetHTML(url)
        try:
            page_items =  html.find("ul", class_="list-unstyled list-wrap").find_all("li", class_="list ")
            return page_items
        except:
            print("НЕТ ЭЛЕМЕНТОВ:", url)
            return []