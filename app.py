from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from colorama import *
from datetime import datetime, timedelta
from fake_useragent import FakeUserAgent
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedError,
    UserDeactivatedBanError,
    UnauthorizedError
)
from telethon.functions import messages
from telethon.sync import TelegramClient
from telethon.types import (
    InputBotAppShortName,
    AppWebViewResultUrl
)
from urllib.parse import unquote
import asyncio, json, os, sys

class TonKombat:
    def __init__(self) -> None:
        config = json.load(open('config.json', 'r'))
        self.api_id = int(config['api_id'])
        self.api_hash = config['api_hash']
        self.pet_active_skill = config['pet_active_skill']
        self.auto_upgrade = config['auto_upgrade']
        self.auto_fight = config['auto_fight']
        self.equipments_names = config['equipments_names']
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'liyue.tonkombat.com',
            'Origin': 'https://staggering.tonkombat.com',
            'Pragma': 'no-cache',
            'Priority': 'u=3, i',
            'Referer': 'https://staggering.tonkombat.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': FakeUserAgent().random
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    async def generate_query(self, session: str):
        try:
            client = TelegramClient(session=f'sessions/{session}', api_id=self.api_id, api_hash=self.api_hash)
            try:
                if not client.is_connected():
                    await client.connect()

                    me = await client.get_me()
                    name = me.first_name if me.first_name is not None else me.username
            except (AuthKeyUnregisteredError, UnauthorizedError, UserDeactivatedBanError, UserDeactivatedError) as error:
                raise error

            webapp_response: AppWebViewResultUrl = await client(messages.RequestAppWebViewRequest(
                peer='Ton_kombat_bot',
                app=InputBotAppShortName(bot_id=await client.get_input_entity('Ton_kombat_bot'), short_name='app'),
                platform='ios',
                write_allowed=True,
                start_param='6094625904'
            ))
            query = unquote(string=webapp_response.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            if client.is_connected():
                await client.disconnect()

            return (name, query)
        except Exception as error:
            await client.disconnect()
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {session} Unexpected Error While Generating Query With Telethon: {str(error)} ]{Style.RESET_ALL}")
            return None

    async def generate_queries(self, sessions):
        tasks = [self.generate_query(session) for session in sessions]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def daily(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/daily'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    if response.status == 400:
                        error_daily = await response.json()
                        if error_daily['message'] == 'already claimed for today':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Already Claimed Daily Bonus For Today ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    daily = await response.json()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {float(daily['data']['amount'] / 1000000000)} From Daily Bonus ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Season: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Season: {str(error)} ]{Style.RESET_ALL}")

    async def upgrades(self, query: str, type: str):
        url = 'https://liyue.tonkombat.com/api/v1/upgrades'
        data = json.dumps({'type':type})
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 400:
                        error_upgrades = await response.json()
                        if error_upgrades['message'] == 'not enough tok to upgrade':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Not Enough TOK To Upgrade {type} ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Upgrade {type} ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Upgrades: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Upgrades: {str(error)} ]{Style.RESET_ALL}")

    async def season_start(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/season/start'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': '0',
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError):
            return False

    async def users_onboard(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/users/onboard'
        data = json.dumps({'house_id':6})
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError):
            return False

    async def users_balance(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/users/balance'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientResponseError as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Balance Users: {str(error)} ]{Style.RESET_ALL}")
            return None
        except Exception as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Balance Users: {str(error)} ]{Style.RESET_ALL}")
            return None

    async def users_claim(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/users/claim'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    if response.status == 400:
                        error_users_claim = await response.json()
                        if error_users_claim['message'] == 'claim too early':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claim Too Early ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    users_claim = await response.json()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {float(users_claim['data']['amount'] / 1000000000)} From Mining ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Users: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Users: {str(error)} ]{Style.RESET_ALL}")

    async def users_stars_spend(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/users/stars/spend'
        data = json.dumps({'type':'upgrade-army-rank'})
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 400:
                        error_users_stars_spend = await response.json()
                        if error_users_stars_spend['message'] == 'not enough stars to upgrade':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Not Enough Stars To Upgrade Rank ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    users_stars_spend = await response.json()
                    if users_stars_spend['data']:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Upgrade Rank ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Users: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Users: {str(error)} ]{Style.RESET_ALL}")

    async def combats_me(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/combats/me'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    combats_me = await response.json()
                    if combats_me['data']['pet']['active_skill'] != self.pet_active_skill:
                        await self.combats_pets_skill(query=query)
                    await self.combats_energy(query=query)
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Combats Me: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Combats Me: {str(error)} ]{Style.RESET_ALL}")

    async def combats_pets_skill(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/combats/pets/skill'
        data = json.dumps({'skill':self.pet_active_skill})
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.patch(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    combats_pets_skill = await response.json()
                    if combats_pets_skill['data']:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Activate Pet Skill {self.pet_active_skill} ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Me Combats: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Me Combats: {str(error)} ]{Style.RESET_ALL}")

    async def combats_energy(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/combats/energy'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    combats_energy = await response.json()
                    if combats_energy['data']['current_energy'] == 0 and datetime.fromisoformat(combats_energy['data']['next_refill'].replace('Z', '+00:00')).astimezone().timestamp() > datetime.now().astimezone().timestamp():
                        return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Can Be Fight At {datetime.fromisoformat(combats_energy['data']['next_refill'].replace('Z', '+00:00')).astimezone().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
                    return await self.combats_find(query=query)
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Combats Energy: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Combats Energy: {str(error)} ]{Style.RESET_ALL}")

    async def combats_find(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/combats/find'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Type': 'application/json'
        }
        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                    async with session.get(url=url, headers=headers, ssl=False) as response:
                        if response.status == 400:
                            error_combats_find = await response.json()
                            if error_combats_find['message'] == 'out of energies':
                                return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Out Of Energies ]{Style.RESET_ALL}")
                        response.raise_for_status()
                        await asyncio.sleep(10)
                        await self.combats_fight(query=query)
            except ClientResponseError as error:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Combats Find: {str(error)} ]{Style.RESET_ALL}")
            except Exception as error:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Combats Find: {str(error)} ]{Style.RESET_ALL}")

    async def combats_fight(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/combats/fight'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    if response.status == 400:
                        error_combats_fight = await response.json()
                        if error_combats_fight['message'] == 'match not found':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Match Not Found ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    combats_fight = await response.json()
                    if combats_fight['data']['winner'] == 'attacker':
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You Beat {combats_fight['data']['enemy']['username']} And Your Rank Gained {combats_fight['data']['rank_gain']} ]{Style.RESET_ALL}")
                    return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You Lost To {combats_fight['data']['enemy']['username']} ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Combats Fight: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Combats Fight: {str(error)} ]{Style.RESET_ALL}")

    async def equipments_me(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/equipments/me'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    equipments_me = await response.json()
                    for equipments_name in self.equipments_names:
                        await self.equipments_status(query=query, name=equipments_name)
                    for equipment in equipments_me['data']:
                        await self.equipments_equip(query=query, equipment_id=equipment['id'], equipment_name=equipment['name'])
                    await self.combats_me(query=query)
        except ClientResponseError as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Equipments Me: {str(error)} ]{Style.RESET_ALL}")
            return None
        except Exception as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Equipments Me: {str(error)} ]{Style.RESET_ALL}")
            return None

    async def equipments_equip(self, query: str, equipment_id: str, equipment_name: str):
        url = f'https://liyue.tonkombat.com/api/v1/equipments/{equipment_id}/equip'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.patch(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    equipments_equip = await response.json()
                    if equipments_equip['data']:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ {equipment_name} Equipped ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Equipments Equip: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Equipments Equip: {str(error)} ]{Style.RESET_ALL}")

    async def equipments_status(self, query: str, name: str):
        url = f'https://liyue.tonkombat.com/api/v1/equipments/{name}/status'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    equipments_status = await response.json()
                    if equipments_status['data'] == 'claimable':
                        return await self.equipments_claim(query=query, name=name)
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Equipments: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Equipments: {str(error)} ]{Style.RESET_ALL}")

    async def equipments_claim(self, query: str, name: str):
        url = f'https://liyue.tonkombat.com/api/v1/equipments/{name}/claim'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    if response.status == 400:
                        error_claim_equipments = await response.json()
                        if error_claim_equipments['message'] == 'non-claimable':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {name} Non-Claimable ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    claim_equipments = await response.json()
                    if claim_equipments['data']:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {name} From Equipments ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Equipments: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Equipments: {str(error)} ]{Style.RESET_ALL}")

    async def tasks_progresses(self, query: str):
        url = 'https://liyue.tonkombat.com/api/v1/tasks/progresses'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    tasks_progresses = await response.json()
                    for task in tasks_progresses['data']:
                        if task['task_user'] is None or (task['task_user']['reward_amount'] == 0 and task['task_user']['repeats'] == 0):
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Starting {task['name']} ]{Style.RESET_ALL}")
                            await self.tasks(query=query, task_id=task['id'])
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Tasks: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Tasks: {str(error)} ]{Style.RESET_ALL}")

    async def tasks(self, query: str, task_id: str):
        url = f'https://liyue.tonkombat.com/api/v1/tasks/{task_id}'
        headers = {
            **self.headers,
            'Authorization': f'tma {query}',
            'Content-Length': '0'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError):
            return False

    async def main(self):
        while True:
            try:
                sessions = [file for file in os.listdir('sessions/') if file.endswith('.session')]
                if not sessions:
                    raise FileNotFoundError("No Session Files Found In The Folder! Please Make Sure There Are '*.session' Files In The Folder.")
                accounts = await self.generate_queries(sessions=sessions)
                total_balance = 0.0

                for (name, query) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    await self.users_onboard(query=query)
                    await self.season_start(query=query)
                    await self.daily(query=query)
                    await self.users_claim(query=query)
                    await self.users_stars_spend(query=query)

                for (name, query) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Earn ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    await self.tasks_progresses(query=query)

                if self.auto_fight:
                    for (name, query) in accounts:
                        self.print_timestamp(
                            f"{Fore.WHITE + Style.BRIGHT}[ Fight ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                        )
                        await self.equipments_me(query=query)

                if self.auto_upgrade:
                    for (name, query) in accounts:
                        self.print_timestamp(
                            f"{Fore.WHITE + Style.BRIGHT}[ Upgrades ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                        )
                        for type in ['pocket-size', 'mining-tok']:
                            await self.upgrades(query=query, type=type)

                for (name, query) in accounts:
                    users_balance = await self.users_balance(query=query)
                    total_balance += float(users_balance['data'] / 1000000000) if users_balance is not None else 0.0

                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ Total Account {len(accounts)} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Total Balance {total_balance} ]{Style.RESET_ALL}"
                )
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {(datetime.now().astimezone() + timedelta(seconds=3600)).strftime('%x %X %Z')} ]{Style.RESET_ALL}")

                await asyncio.sleep(3600)
                self.clear_terminal()
            except Exception as error:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(error)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        init(autoreset=True)
        tonkombat = TonKombat()
        asyncio.run(tonkombat.main())
    except (ValueError, IndexError, FileNotFoundError) as error:
        tonkombat.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(error)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)