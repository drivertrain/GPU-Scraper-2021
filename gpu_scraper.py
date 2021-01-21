from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import datetime
from PIL import Image, ImageOps
from playsound import playsound
import pytesseract
import asyncio
import sys
from threading import Thread
from functools import partial
from colorama import Fore

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)


async def wait_one_second():
    await asyncio.sleep(1)
    # print("...", flush=True)
    return


def remove_colors(image, colors, replacement=(255, 255, 255)):
    image_data = image.load()
    h, w = image.size
    for x in range(h):
        for y in range(w):
            r, g, b, a = image_data[x, y]
            for color in colors:
                if (r, g, b) == color:
                    (r, g, b) = replacement
                    image_data[x, y] = r, g, b, a
    return image


def contains_color(image, colors):
    image_data = image.load()
    h, w = image.size
    for x in range(h):
        for y in range(w):
            r, g, b, a = image_data[x, y]
            for color in colors:
                if (r, g, b) == color:
                    return True
    return False


class GPU:
    def __init__(self, **kwargs):
        self.link = kwargs.get(
            "link",
            "https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440",
        )
        self.given_name = kwargs.get("name", "3080FE")

    def __repr__(self, **kwargs):
        return self.given_name

    @property
    def name(self):
        return self.given_name.replace(" ", "")

    @property
    def path(self):
        invalid = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        path = self.name
        for char in invalid:
            path = path.replace(char, "")

        return path + ".png"


class GPUScraper:
    def __init__(self, interval, targets):
        self.wait_interval = interval
        self.targets = targets
        self.path = ""
        self.provider = ""
        self.error_count = 0
        return

    async def initialize(self, **kwargs):
        driver = webdriver.Chrome("./chromedriver")
        driver.set_window_position(0, 0)
        driver.set_window_size(800, 600)
        self.driver = driver
        return

    def play_alarm(self):
        playsound("annoying.mp3")

    async def check_stock(self, **kwargs):
        strformat = Fore.LIGHTYELLOW_EX + "%-10s "+ Fore.CYAN+ "%-25s %-10s"
        for target in self.targets:
            try:
                result = await self.check_gpu(target)
                if result:
                    self.play_alarm()
                    print(target.link, flush=True)
                    print(strformat % (self.provider, target.given_name+, Fore.GREEN + "In Stock"),
                        flush=True,
                    )
                else:
                    print(strformat % (self.provider, target.given_name, Fore.YELLOW + "Out of Stock"),
                        flush=True,
                    )
            except:
                print(
                    strformat % (self.provider, target.given_name, Fore.RED + "ERROR FETCHING"),
                    flush=True,
                )
                self.error_count += 1
        return

    async def check_gpu(self, target):
        return

    async def main(self):
        previous_check = start_time = datetime.datetime.now()
        await self.initialize()
        trials = 0
        while True:
            if trials % 10 == 0:
                print(
                    "{} Checked {} times over: {} (HH:MM:SS:MS)".format(
                        self.provider, trials, datetime.datetime.now() - start_time
                    ),
                    flush=True,
                )

            # Reset Error Count Periodically
            if (datetime.datetime.now() - previous_check).seconds >= (30 * 60):
                previous_check = datetime.datetime.now()
                self.error_count = 0

            # If more than 5 errors, do nothing until error count is reset
            if self.error_count > 5:
                continue
            else:
                await self.check_stock()
                trials += 1

            # Wait the given interval at the end of each interation
            for x in range(self.wait_interval):
                await wait_one_second()
        return


class BBScraper(GPUScraper):
    def __init__(self, interval, targets):
        super().__init__(interval, targets)
        self.path = "img/bestbuy/"
        self.provider = "BestBuy"

    async def validate(self, target):
        # look for the yellow color that would be on add to cart button to verify
        bb_yellow = (255, 224, 0)
        image = Image.open(self.path + target.path)
        return contains_color(image, colors=[bb_yellow])

    async def check_gpu(self, target):
        colors_to_rid = [(197, 203, 213), (43, 93, 245)]
        driver = self.driver
        driver.get(target.link)
        button = driver.find_element_by_class_name("fulfillment-add-to-cart-button")
        button.screenshot(self.path + target.path)
        await wait_one_second()
        button.screenshot(self.path + target.path)
        # get rid of gray color that stops text recognition
        converted = remove_colors(
            Image.open(self.path + target.path),
            colors=colors_to_rid,
            replacement=(255, 255, 255),
        )
        text = pytesseract.image_to_string(converted).strip()
        if text == "":
            return await self.check_gpu(target)
        else:
            if "sold out" in text.lower():
                return False
            else:
                return await self.validate(target)


class BandHScraper(GPUScraper):
    def __init__(self, interval, targets):
        super().__init__(30, targets)
        self.path = "img/bandh/"
        self.provider = "B&H"

    async def validate(self, target):
        bandh_blue = (10, 146, 202)
        image = Image.open(self.path + target.path)
        return contains_color(image, colors=[bandh_blue])

    async def check_gpu(self, target):
        driver = self.driver
        driver.get(target.link)
        for x in range(30):
            await wait_one_second()
        button = driver.find_element_by_class_name("cartRow_2dS2mdogHYAqhmKoANr6Ol")
        button.screenshot(self.path + target.path)
        await wait_one_second()
        button.screenshot(self.path + target.path)
        text = pytesseract.image_to_string(Image.open(self.path + target.path)).strip()
        if "notify" or "cart" in text.lower():
            if "add to cart" in text.lower():
                return await self.validate(target)
            else:
                return False


class NeweggScraper(GPUScraper):
    def __init__(self, interval, targets):
        super().__init__(interval, targets)
        self.path = "img/newegg/"
        self.provider = "Newegg"

    async def check_gpu(self, target):
        driver = self.driver
        driver.get(target.link)
        button = driver.find_element_by_class_name("product-inventory")
        button.screenshot(self.path + target.path)
        await wait_one_second()
        button.screenshot(self.path + target.path)
        text = pytesseract.image_to_string(Image.open(self.path + target.path)).strip()
        if "in stock" in text.lower():
            return True
        elif "out of stock" in text.lower():
            return False
        else:
            return await self.check_gpu(target)


def run_multithreaded():
    try:
        config = eval(open("scraper_config.json").read())
    except:
        print("Couldn't open config...only checking 3080FE")
        config = {"no_config": None}

    wait_interval = config.get("interval", 10)

    best_buy = []
    b_and_h = []
    newegg = []

    for target in config.get("targets", [{"n/a": "n/a"}]):
        for link in target["links"]:
            gpu = GPU(name=target["name"], link=link)
            if "newegg" in gpu.link:
                newegg.append(gpu)
            elif "bhphotovideo" in gpu.link:
                b_and_h.append(gpu)
            elif "bestbuy" in gpu.link:
                best_buy.append(gpu)

    scraper1 = BBScraper(interval=wait_interval, targets=best_buy)
    scraper2 = BandHScraper(interval=wait_interval, targets=b_and_h)
    scraper3 = NeweggScraper(interval=wait_interval, targets=newegg)

    thread_1_target = partial(asyncio.run, scraper1.main())
    thread_2_target = partial(asyncio.run, scraper2.main())
    thread_3_target = partial(asyncio.run, scraper3.main())

    threads = [
        Thread(target=thread_1_target, name="BestBuyScraper"),
        Thread(target=thread_2_target, name="BandHScraper"),
        Thread(target=thread_3_target, name="NeweggScraper"),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
    return


def debug():
    asus_ekwb = GPU(
        name="ASUS EKWB 3080",
        link="https://www.newegg.com/asus-geforce-rtx-3080-rtx3080-10g-ek/p/N82E16814126488",
    )
    scraper = NeweggScraper(interval=5, targets=[asus_ekwb])
    asyncio.run(scraper.main())


if __name__ == "__main__":
    # debug()
    run_multithreaded()
