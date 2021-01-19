from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import datetime
from PIL import Image, ImageOps
from playsound import playsound
import pytesseract
import asyncio
import sys

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)


async def wait_one_second():
    await asyncio.sleep(1)
    # print("...", flush=True)
    return


class GPU:
    def __init__(self, **kwargs):
        self.link = kwargs.get(
            "link",
            "https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440",
        )
        self.name = kwargs.get("name", "3080FE")

    def __repr__(self, **kwargs):
        return self.name


class GPUScraper:
    def __init__(self, *args, **kwargs):
        self.wait_interval = kwargs.get("interval", 10)
        self.targets = []
        for target in kwargs.get("targets", [{"n/a": "n/a"}]):
            self.targets.append(GPU(**target))
        print(self.targets)
        return

    async def initialize(self, **kwargs):
        driver = webdriver.Chrome("./chromedriver")
        driver.set_window_position(0, 0)
        driver.set_window_size(800, 600)
        self.driver = driver

        return

    async def check_yellow(self, target):
        # look for the yellow color that would be on add to cart button to verify
        bb_yellow = (255, 224, 0)
        image = Image.open("current_{}.png".format(target.name))
        image_data = image.load()
        h, w = image.size
        for x in range(h):
            for y in range(w):
                r, g, b, a = image_data[x, y]
                if (r, g, b) == bb_yellow:
                    print("Add to Cart Yellow Found On Screen", flush=True)
                    return True
        return False

    def play_alarm(self):
        playsound("annoying.mp3")

    async def check_stock(self, **kwargs):

        # print("Checking Stock", flush=True)
        for target in self.targets:
            result = ""
            while result == "":
                result = await self.get_text(target)
            print("{}: {}".format(target.name, result), flush=True)
            if "sold out" in result.lower():
                pass
            else:
                if await self.check_yellow(target):
                    self.play_alarm()

        return

    async def get_text(self, target):
        def convert_image(taget, image):
            # convert grey color to white
            image_data = image.load()
            h, w = image.size
            for x in range(h):
                for y in range(w):
                    r, g, b, a = image_data[x, y]
                    if (r == 197) and (g == 203) and (b == 213):
                        r = 255
                        g = 255
                        b = 255
                    if (r == 43) and (g == 93) and (b == 245):
                        r = 255
                        g = 255
                        b = 255

                    image_data[x, y] = r, g, b, a
            image.save("curr_fixed_%s.png" % target.name)
            return

        driver = self.driver
        driver.get(target.link)
        await wait_one_second()
        button = driver.find_element_by_class_name("fulfillment-add-to-cart-button")
        button.screenshot("current_{}.png".format(target.name))
        # get rid of gray color that stops text recognition
        convert_image(target, Image.open("current_{}.png".format(target.name)))
        text = pytesseract.image_to_string(
            Image.open("curr_fixed_{}.png".format(target.name))
        )
        return text.strip()

    async def main(self):
        start_time = datetime.datetime.now()
        await self.initialize()
        still_need = True
        trials = 0
        while still_need:
            trials += 1
            if trials % 10 == 0:
                print(
                    "Checked {} times over: {} (HH:MM:SS:MS)".format(
                        trials, datetime.datetime.now() - start_time
                    ),
                    flush=True,
                )
            await self.check_stock()
            for x in range(self.wait_interval):
                await wait_one_second()
        return


if __name__ == "__main__":
    try:
        config = eval(open("scraper_config.json").read())
    except e:
        print("Couldn't open config...only checking 3080FE")
        config = {"no_config": None}

    scraper = GPUScraper(**config)
    asyncio.run(scraper.main())
