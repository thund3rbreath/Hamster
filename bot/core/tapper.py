import asyncio
import json
import random
import sys
import threading
import traceback
from itertools import cycle
from urllib.parse import unquote

import aiohttp
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.types import InputBotAppShortName
from pyrogram.raw.functions.messages import RequestAppWebView

from bot.core.agents import generate_random_user_agent
from bot.config import settings
import time as time_module

from bot.utils.utilities import DetectOS, GenerateHKFingerprint
from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from random import randint
from .PromoGames import PromoGames
from .GenerateKeys import Playground
from datetime import datetime
from .HttpRequests import HttpRequest

class Tapper:
    def __init__(self, tg_client: Client, multi_thread: bool, playground: Playground | None):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.first_name = ''
        self.last_name = ''
        self.user_id = ''
        self.auth_token = ""
        self.last_claim = None
        self.last_checkin = None
        self.balace = 0
        self.maxtime = 0
        self.fromstart = 0
        self.new_usr = False
        self.balance = 0
        self.multi_thread = multi_thread
        self.my_ref = "kentId6624523270"
        self.authToken = ""
        self.account_info = None
        self.cf_version = None
        self.tg_web_data = None
        self.http = None
        self.playground = playground


    async def get_tg_web_data(self, proxy: str | None) -> str:
        try:
            if settings.REF_LINK == "":
                ref_param = "kentId6624523270"
            else:
                ref_param = settings.REF_LINK.split("=")[1]
        except:
            logger.error(f"{self.session_name} | Ref link invaild please check again !")
            sys.exit()

        actual = random.choices([self.my_ref, ref_param], weights=[30, 70]) # edit this line to [0, 100] if you don't want to support me
        self.ref = actual[0]
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict
        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('hamster_kombat_bot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"<light-yellow>{self.session_name}</light-yellow> | FloodWait {fl}")
                    logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotAppShortName(bot_id=peer, short_name="start"),
                platform='android',
                write_allowed=True,
                start_param=actual[0]
            ))

            auth_url = web_view.url
            # print(auth_url)
            tg_web_data1 = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data1

        except InvalidSession as error:
            raise error

        except Exception as error:
            traceback.print_exc()
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: "
                         f"{error}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy):
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5), )
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")
            return False

    def ip(self):

        logger.info(f"{self.session_name} | 🌍 <yellow>Getting IP ...</yellow>")
        response = self.http.get(
            url="/ip", valid_option_response_code=200, auth_header=False
        )

        if response is None:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get IP!</red>")
            return None

        logger.info(
            f"{self.session_name} | 🌍 <green>IP: <yellow>{response['ip']}</yellow>, Country: <yellow>{response['country_code']}</yellow></green>"
        )

        return response

    def login(self, web_app_query):
        logger.info(f"{self.session_name} | 🔑 <yellow>Logging in to HamsterKombat bot ...</yellow>")

        try:
            DetectedOS = DetectOS(self.http.user_agent)
            logger.info(f"{self.session_name} | 📱 <green> Logging in as <yellow>{DetectedOS}</yellow> device!</green>")
            HKFingerprint = GenerateHKFingerprint(DetectedOS)
            HKFingerprint["initDataRaw"] = web_app_query
            login_data = self.http.post(
                url="/auth/auth-by-telegram-webapp",
                payload=json.dumps(HKFingerprint),
                headers={"authorization": ""},
                auth_header=False,
            )

            if (
                    login_data is None
                    or "authUserId" not in login_data
                    or "authToken" not in login_data
            ):
                logger.error(f"{self.session_name} | 🔑 <red>Failed to login to HamsterKombat bot!</red>")
                return None

            logger.info(
                f"{self.session_name} | ✅ <green>Successfully logged in to HamsterKombat bot, UserID: </green><cyan>{login_data['authUserId']}</cyan>"
            )

            return login_data
        except Exception as e:
            logger.error(f"{self.session_name} | 🔑 <red>Failed to login to HamredKombat bot: {e}</red>")
            return None

    def get_account_info(self):
        logger.info(f"{self.session_name} | 🗒️ <yellow>Getting account info ...</yellow>")
        response, headers = self.http.post(
            url="auth/account-info",
            return_headers=True,
        )

        if response is None or "accountInfo" not in response:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get account info!</red>")
            return None, None

        date = response["accountInfo"]["at"].split("T")[0].replace("-", "/")
        logger.info(
            f"{self.session_name} | 🗒️ <green>Account ID: <cyan>{response['accountInfo']['id']}</cyan>, Join Date: <cyan>{date}</cyan></green>"
        )

        if headers is None:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get account info headers!</red>")
            return None, None

        return response, headers["interlude-config-version"]


    def get_sync(self):
        logger.info(f"{self.session_name} | 🔄 <yellow>Getting sync ...</yellow>")

        response = self.http.post(
            url="interlude/sync",
        )

        if response is None or "interludeUser" not in response:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get sync!</red>")
            return None

        return response["interludeUser"]

    def get_referral_info(self):
        logger.info(f"{self.session_name} | 🔄 <yellow>Getting referral info ...</yellow>")

        response = self.http.post(
            url="interlude/referrer-info",
        )

        if response is None:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get referral info!</red>")
            return None

        return response

    def set_select_exchange(self, exChangeId):
        logger.info(f"{self.session_name} | 🔄 <yellow>Setting exchange ...</yellow>")
        response = self.http.post(
            url="interlude/select-exchange",
            payload=json.dumps(
                {
                    "exchangeId": exChangeId,
                }
            ),
        )

        if response is None:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to set exchange!</red>")
            return None

        return response

    def get_promos(self):
        logger.info(f"{self.session_name} | 🔄 <yellow>Getting promos ...</yellow>")

        response = self.http.post(
            url="interlude/get-promos",
        )

        if response is None or "promos" not in response:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get promos!</red>")
            return None

        return response

    def get_version_config(self, version):
        logger.info(
            f"{self.session_name} | 🔄 <yellow>Getting config version: <cyan>{version}</cyan> ...</yellow>"
        )

        response = self.http.get(
            url=f"interlude/config/{version}",
        )

        if response is None and "config" not in response:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get config!</red>")
            return None

        return response

    def get_config(self):
        logger.info(f"{self.session_name} | 🔄 <yellow>Getting config ...</yellow>")

        response = self.http.post(
            url="interlude/config",
        )

        if response is None or "dailyKeysMiniGames" not in response:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get config!</red>")
            return None

        return response

    def get_upgrades_for_buy(self):
        logger.info(f"{self.session_name} | 🔄 <yellow>Getting upgrades ...</yellow>")

        response = self.http.post(
            url="interlude/upgrades-for-buy",
        )

        if response is None or "upgradesForBuy" not in response:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get upgrades!</red>")
            return None

        return response

    def get_list_tasks(self):
        logger.info(f"{self.session_name} | 🔄 <yellow>Getting tasks ...</yellow>")

        response = self.http.post(
            url="interlude/list-tasks",
        )

        if response is None or "tasks" not in response:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get tasks!</red>")
            return None

        return response

    def get_list(self, ip_data):
        logger.info(f"{self.session_name} | 🔄 <yellow>Getting list ...</yellow>")

        response = self.http.post(
            url="interlude/withdraw/list",
            payload=json.dumps(
                {
                    "ipInfo": ip_data,
                }
            ),
        )

        if response is None:
            logger.error(f"{self.session_name} | 🔴 <red>Failed to get list!</red>")
            return None

        return response

    def get_skin(self):
        logger.info(f"{self.session_name} | 🔄 <yellow>Getting skin ...</yellow>")

        response = self.http.post(
            url="interlude/get-skin",
        )

        if response is None or "skins" not in response:
            logger.error(f"{self.session_name}🔴 <red>Failed to get skin!</red>")
            return None

        return response

    def get_available_cards(self, cards):
        new_cards = []
        for card in cards:
            if not card.get("isAvailable", True):
                continue

            if card.get("isExpired", False):
                continue

            if card.get("cooldownSeconds", 0) > 0:
                continue

            if card.get("maxLevel") is not None:
                if card.get("level", 0) >= card.get("maxLevel"):
                    continue

            new_cards.append(card)

        return new_cards

    def get_card_coefficient(self, card):
        if card["price"] == 0 or card["profitPerHourDelta"] == 0:
            return 0
        return card["price"] / card["profitPerHourDelta"]


    def filter_by_balance(self, cards, balance):
        potential_price = 0
        potential_profit = 0
        for i in reversed(range(len(cards))):
            upgrade_cost = cards[i]["price"]
            upgrade_profit = cards[i]["profitPerHourDelta"]
            if potential_price + upgrade_cost <= balance:
                potential_price += upgrade_cost
                potential_profit += upgrade_profit
            else:
                del cards[i]

    def filter_by_coefficient(self, cards):
        coefficient_limit = settings.UPGRADE_COEFFICIENT
        expensive_cards = []

        for i in reversed(range(len(cards))):
            card_coefficient = self.get_card_coefficient(cards[i])
            if card_coefficient > coefficient_limit:
                expensive_cards.append(cards[i])
                del cards[i]

        if expensive_cards:
            expensive_card_names = ", ".join(
                [f"<c>{card['name']}</c>" for card in expensive_cards]
            )
            logger.info(
                f"{self.session_name} | 🪙 <yellow>Cards {expensive_card_names} exceed the upgrade coefficient ({coefficient_limit}).</yellow>"
            )
            logger.info(
                f"🪙 <yellow>You can adjust the coefficient in settings.</yellow>"
            )

    def sort_cards(self, cards):
        return cards.sort(key=lambda x: x["price"] / x["profitPerHourDelta"])

    def buy_card(self, card):
        if card is None or "id" not in card:
            logger.error(f"{self.session_name} | ❌ <red>Card not found!</red>")
            return False

        cardId = card["id"]
        cardName = card["name"]
        cardPrice = card["price"]
        cardLevel = card["level"]

        logger.info(
            f"{self.session_name} | 💳 <green>Start upgrading card <cyan>{cardName}</cyan> to level <cyan>{cardLevel}</cyan> for <cyan>{cardPrice:.2f}💎</cyan></green>"
        )
        response = self.http.post(
            url="interlude/buy-upgrade",
            payload=json.dumps(
                {
                    "upgradeId": cardId,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                    - random.randint(100, 1000),
                }
            ),
        )

        if response is None or "interludeUser" not in response:
            logger.error(f"{self.session_name} | ❌ <red>Failed to buy card!</red>")
            return False

        logger.info(
            f"{self.session_name} | 💰 <green>Card <cyan>{card['name']}</cyan> was upgraded to level <cyan>{card['level']}</cyan> for <cyan>{card['price']:.2f}💎</cyan></green>"
        )
        return True

    def start_upgrades(self, balance):
        logger.info(f"{self.session_name} | 🔝 <yellow>Starting upgrade ...</yellow>")
        spent_amount = 0
        profit_per_hour = 0
        basic = self.get_upgrades_for_buy()
        if basic is None or "upgradesForBuy" not in basic:
            return

        cards = self.get_available_cards(basic["upgradesForBuy"])
        if not cards or len(cards) == 0:
            logger.info(f"{self.session_name} | 💸 <yellow>No upgrades available ...</yellow>")
            return

        self.filter_by_balance(cards, balance)
        if not cards or len(cards) == 0:
            logger.info(f"{self.session_name} | 💴 <yellow>No upgrades available ...</yellow>")
            return

        self.filter_by_coefficient(cards)
        if not cards or len(cards) == 0:
            logger.info(f"{self.session_name}💴 <yellow>No upgrades available ...</yellow>")
            return

        self.sort_cards(cards)
        cards_price = sum(card['price'] for card in cards)
        cards_profit = sum(card['profitPerHourDelta'] for card in cards)
        logger.info(
            f"==={self.session_name}==="
            f"💸 <green>Available cards: <cyan>{len(cards)}</cyan> "
            f"with total price <cyan>{cards_price:.2f}💎</cyan> "
            f"and profit <cyan>+{cards_profit:.2f}💎</cyan></green>"
        )

        buy_errors = 0
        for best_card in cards:
            time_module.sleep(5)
            buy_card = self.buy_card(best_card)
            if not buy_card:
                if buy_errors >= 3:
                    logger.error(
                        f"{self.session_name} | ❌ <red>Buying cards has been interrupted due to errors ({buy_errors}).</red>"
                    )
                    break
                continue
            spent_amount = spent_amount + best_card["price"]
            profit_per_hour = profit_per_hour + best_card["profitPerHourDelta"]
            time_module.sleep(5)

    def claim_task(self, task_id, user_tasks):
        if not task_id or not user_tasks:
            return

        for task in user_tasks:
            if task["id"] == task_id and task["isCompleted"]:
                return

        logger.info(f"{self.session_name} | 📝 <yellow>Claiming task <cyan>{task_id}</cyan> ...</yellow>")

        resp = self.http.post(
            url="/interlude/check-task",
            payload=json.dumps({"taskId": task_id}),
        )

        logger.info(f"{self.session_name} | 📝 <green>Task <cyan>{task_id}</cyan> claimed!</green>")


    def start_tasks(self, tasks, user_tasks):
        logger.info(f"{self.session_name} | 📝 <yellow>Starting tasks ...</yellow>")
        if not tasks:
            logger.error(f"{self.session_name} | 🟡 <yellow>Tasks not found!</yellow>")

        for task in tasks:
            task_id = task["id"]
            task_type = task["type"]

            if task_type not in {"WithLink", "WithLocaleLink"}:
                continue

            self.claim_task(task_id, user_tasks)

        logger.info(f"{self.session_name} | ✅ <green>All tasks completed!</green>")

    def clean_promos(self, promos):
        states = promos["states"]
        promos = promos["promos"]
        final_promos = []
        for promo in promos:
            promo_name = promo["title"]["en"]
            if promo["promoId"] not in PromoGames:
                logger.info(
                    f"{self.session_name} | 🟡 <yellow>Unsupported promo <green>{promo_name}</green> game...</yellow>"
                )
                continue

            receiveKeysToday = 0
            for state in states:
                if state["promoId"] == promo["promoId"] and "receiveKeysToday" in state:
                    receiveKeysToday = state["receiveKeysToday"]
                    break

            if int(receiveKeysToday) >= int(promo["rewardsPerDay"]):
                logger.info(f"{self.session_name} | ✅ <green>Max keys reached for <cyan>{promo_name}</cyan>...</green>")
                continue

            final_promos.append(promo)

        return final_promos

    def apply_promo(self, promoCode):
        logger.info(f"{self.session_name} | 🎲 <yellow>Applying promo code <green>{promoCode}</green>...</yellow>")

        response = self.http.post(
            url="interlude/apply-promo",
            payload=json.dumps({"promoCode": promoCode}),
        )

        if response is None or "reward" not in response:
            logger.error(
                f"{self.session_name} | 🔴 <red>Failed to apply promo code <yellow>{promoCode}</yellow>!</red>"
            )
            return False

        logger.info(f"{self.session_name} | ✅ <green>Applied promo code <yellow>{promoCode}</yellow>!</green>")
        return True

    def add_to_queue(self, promo):
        try:
            if self.playground.add_request(
                promo["promoId"], self.http.proxy, self.http.user_agent
            ):
                return True

            return False
        except Exception as e:
            logger.error(f"{self.session_name}🔴 <red>Error claiming Playground: {e}</red>")

        return False

    def claim_random(self):
        try:
            promos = self.get_promos()
            if promos is None:
                return

            promos = self.clean_promos(promos)
            if not promos or len(promos) == 0:
                logger.info(f"{self.session_name} | 🟢 <yellow>No promos to claim!</yellow>")
                return

            promoCodeResponse = self.playground.get_not_used_request(
                proxy=self.http.proxy
            )

            if promoCodeResponse is not None:
                promoCode = promoCodeResponse["promoCode"]
                promoId = promoCodeResponse["promoId"]

                for promo in promos:
                    if promo["promoId"] == promoId:
                        self.playground.mark_request_as_used(
                            promoId, promoCode
                        )

                        logger.info(
                            f"{self.session_name} | 🔑 <yellow>Claiming Playground with promo code <green>{promoCode}</green>...</yellow>"
                        )

                        self.apply_promo(promoCode)

                        logger.info(
                            f"{self.session_name} | ✅ <green>Claimed Playground with promo code <yellow>{promoCode}</yellow>!</green>"
                        )
                        promos = self.get_promos()
                        if promos is None:
                            return

                        promos = self.clean_promos(promos)
                        if not promos or len(promos) == 0:
                            logger.info(f"{self.session_name} | 🟢 <yellow>No promos to claim!</yellow>")
                            return

            promo = random.choice(promos)
            self.add_to_queue(promo)
        except Exception as e:
            logger.error(f"{self.session_name}🔴 <red>Error claiming random Playground: {e}</red>")

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        headers["User-Agent"] = generate_random_user_agent(device_type='android', browser_type='chrome')
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)


        # session1 = requests.Session()

        if proxy:
            proxy_check = await self.check_proxy(http_client=http_client, proxy=proxy)
            if proxy_check:
                proxy_type = proxy.split(':')[0]
                proxies = {
                    proxy_type: proxy
                }
                self.http = HttpRequest(proxy, headers["User-Agent"])
                logger.info(f"{self.session_name} | bind with proxy ip: {proxy}")
        else:
            self.http = HttpRequest(proxy, headers["User-Agent"])


        token_live_time = randint(3000, 3600)
        while True:
            try:
                if time_module.time() - access_token_created_time >= token_live_time:
                    tg_web_data = await self.get_tg_web_data(proxy=proxy)
                    self.tg_web_data = tg_web_data
                    # await asyncio.sleep(100)
                    access_token_created_time = time_module.time()
                    token_live_time = randint(3000, 3600)

                ip = self.ip()
                if ip is None:
                    await http_client.close()
                    return

                login_data = self.login(self.tg_web_data)
                if login_data is None:
                    await http_client.close()
                    return

                self.authToken = login_data['authToken']
                self.user_id = login_data["authUserId"]
                self.http.authToken = self.authToken

                account_info, interlude_config_version = self.get_account_info()

                if account_info is None or interlude_config_version is None:
                    await http_client.close()
                    return

                sync = self.get_sync()
                if sync is None:
                    await http_client.close()
                    return

                totalDiamonds = sync['totalDiamonds']
                balanceDiamonds = sync["balanceDiamonds"]
                earnPassivePerHour = sync["earnPassivePerHour"]
                tasks = sync["tasks"]

                if "exchangeId" not in sync or sync["exchangeId"] is None:
                    logger.info(f"{self.session_name} | <yellow>👶 Looks account is new</yellow>")
                    logger.info(f"{self.session_name} | <green>🐹 Setting up hamster account</green>")
                    self.get_referral_info()
                    self.set_select_exchange("hamster")

                totalDiamonds_short = "{:.2f}".format(totalDiamonds)
                balanceDiamonds_short = "{:.2f}".format(balanceDiamonds)
                earnPassivePerHour_short = "{:.2f}".format(earnPassivePerHour)

                logger.info(
                    f"{self.session_name} | <green>🔷 Total Diamonds: <cyan>{totalDiamonds_short}💎</cyan>, Balance Diamonds: <cyan>{balanceDiamonds_short}💎</cyan>, Earn Passive Per Hour: <cyan>{earnPassivePerHour_short}</cyan></green>"
                )

                promos = self.get_promos()
                if promos is None:
                    await http_client.close()
                    return

                v_config_data = self.get_version_config(interlude_config_version)
                if v_config_data is None or "config" not in v_config_data:
                    await http_client.close()
                    return

                get_config = self.get_config()
                if get_config is None or "dailyKeysMiniGames" not in get_config:
                    await http_client.close()
                    return

                upgrades_for_buy = self.get_upgrades_for_buy()
                if upgrades_for_buy is None:
                    await http_client.close()
                    return

                list_tasks = self.get_list_tasks()
                if list_tasks is None:
                    await http_client.close()
                    return

                listing = self.get_list(ip)
                if listing is None:
                    await http_client.close()
                    return

                get_skin = self.get_skin()
                if get_skin is None:
                    await http_client.close()
                    return

                logger.info(
                    f"{self.session_name} | <green>✅ Sending basic request to the server was successful!</green>"
                )

                if settings.AUTO_UPGRADE:
                    self.start_upgrades(balanceDiamonds)
                else:
                    logger.info(f"{self.session_name} | <yellow>🔔 Auto upgrade is disabled!</yellow>")

                if settings.AUTO_TASK:
                    self.start_tasks(v_config_data['config']['tasks'], list_tasks['tasks'])
                else:
                    logger.info(f"{self.session_name} | <yellow>🔔 Auto tasks is disabled!</yellow>")

                if settings.AUTO_PLAYGROUND is False:
                    logger.info(f"{self.session_name} | <yellow>🔔 Auto playground is disabled!</yellow>")
                    logger.info(
                        f"<green>🤖 Farming is completed for account <cyan>{self.session_name}</cyan>!</green>"
                    )
                    await http_client.close()
                    return

                if proxy is None:
                    logger.warning(
                        "<yellow>🔔 If you have more than 5 accounts, make sure to use proxies for your accounts.</yellow>"
                    )
                self.claim_random()
                logger.info(
                    f"{self.session_name} | <green>🤖 Farming is completed for account <cyan>{self.session_name}</cyan>!</green>"
                )

                if self.multi_thread:
                    sleep_ = randint(settings.SLEEP_TIME_BETWEEN_EACH_ROUND[0],
                                     settings.SLEEP_TIME_BETWEEN_EACH_ROUND[1])
                    logger.info(
                        f"<green>⌛ Farming for <cyan>{self.session_name}</cyan> completed. Waiting for <cyan>{sleep_}</cyan> seconds before next check...</green>"
                    )
                    await asyncio.sleep(sleep_)
                else:
                    await http_client.close()
                    break


            except InvalidSession as error:
                raise error

            except Exception as error:
                traceback.print_exc()
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))


async def run_tapper(tg_client: Client, proxy: str | None, playground):
    try:
        sleep_ = randint(1, 15)
        logger.info(f"{tg_client.name} | start after {sleep_}s")
        await asyncio.sleep(sleep_)

        await Tapper(tg_client=tg_client, multi_thread=True, playground=playground).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")


async def run_tapper1(tg_clients: list[Client], proxies):
    proxies_cycle = cycle(proxies) if proxies else None
    playground = Playground(f"Key thread")
    if settings.AUTO_PLAYGROUND:
        threading.Thread(target=playground.start).start()
    while True:
        for tg_client in tg_clients:
            try:
                await Tapper(tg_client=tg_client, multi_thread=False, playground=playground).run(
                    next(proxies_cycle) if proxies_cycle else None)

            except InvalidSession:
                logger.error(f"{tg_client.name} | Invalid Session")

            sleep_ = randint(settings.DELAY_EACH_ACCOUNT[0], settings.DELAY_EACH_ACCOUNT[1])
            logger.info(f"Sleep {sleep_}s before running next account.")
            await asyncio.sleep(sleep_)

        sleep_ = randint(settings.SLEEP_TIME_BETWEEN_EACH_ROUND[0], settings.SLEEP_TIME_BETWEEN_EACH_ROUND[1])
        logger.info(f"<red>Sleep {sleep_}s...</red>")

        await asyncio.sleep(sleep_)
