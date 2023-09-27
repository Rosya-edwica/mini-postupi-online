import aiomysql
from aiomysql.connection import Connection

import models

class Database:
    def __init__(self, host: str, port: int, user: str, password: str, dbname: str):
        self.__host = host
        self.__port = port
        self.__user = user
        self.__password = password
        self.__dbname = dbname

        self.connection: Connection = None
    

    async def Connect(self) -> Connection:
        self.connection = await aiomysql.connect(
            host=self.__host,
            port=self.__port,
            user=self.__user,
            password=self.__password,
            db=self.__dbname
        )
        return self.connection
    
    def Close(self) -> None:
        self.connection.close()


    def GetConnection(self) -> Connection | None: 
        if self.connection is None:
            exit("Отсутствует подключение к БД! Для подключения к бд используйте метод Connect()")
        
        return self.connection
    

    async def SaveVuz(self, vuz: models.Vuz):
        query = f"""
            INSERT IGNORE INTO short_vuz(abbr, name, city)
            VALUES ('{vuz.Abbr}', '{vuz.Name}', '{vuz.City}')
        """.strip()
        await self.__execute_query(query)
        print(f"Saved vuz: {vuz.Name}")


    async def SaveSpecialization(self, spec: models.Specialization):
        vuz_id = await self.getVuzIdByAbbr(spec.VuzAbbr)
        query = f"""
            INSERT IGNORE INTO short_specialization(vuz_id, code, name, direction)
            VALUES({vuz_id}, '{spec.Code}', '{spec.Name}', '{spec.Direction}')
        """.strip()
        await self.__execute_query(query)
        print(f"Saved spec: ", spec.Code)

    async def SaveProgram(self, program: models.Program):
        spec_id = await self.getSpecIdByAbbrAndCode(program.VuzAbbr, program.SpecCode)
        query = f"""
            INSERT IGNORE INTO short_program(spec_id, name, level, cost, free_places, payment_places, is_payment, form, duration_in_months, subjects, url)
            VALUES({spec_id}, '{program.Name}', '{program.Level}', {program.Cost}, {program.FreePlaces}, {program.PaymentPlaces}, {program.IsPayment},
            '{program.Form}', {program.DurationInMonths}, '{"|".join(program.Subjects)}', '{program.Url}')
        """.strip()
        await self.__execute_query(query)
        print("Saved program: ", program.Name)

    async def __execute_query(self, query: str):
        connection = self.GetConnection()
        async with connection.cursor() as cursor:
            await cursor.execute(query)
        await connection.commit()

    
    async def getVuzIdByAbbr(self, abbr: str) -> int:
        query = f"SELECT id FROM short_vuz WHERE abbr = '{abbr}'"
        connection = self.GetConnection()
        async with connection.cursor() as cursor:
            await cursor.execute(query)
            res = await cursor.fetchone()
        return res[0]
    
    async def getSpecIdByAbbrAndCode(self, abbr: str, code: str) -> int:
        query = f"""
            SELECT short_specialization.id 
            FROM short_specialization
            LEFT JOIN short_vuz ON short_vuz.id = vuz_id
            WHERE short_vuz.abbr = "{abbr}" AND code = "{code}"
        """.strip()
        connection = self.GetConnection()
        async with connection.cursor() as cursor:
            await cursor.execute(query)
            res = await cursor.fetchone()
        return res[0]