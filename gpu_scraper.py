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
        return self.name

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
        for target in self.targets:
            try:
                result = await self.check_gpu(target)
                if result:
                    self.play_alarm()
                    print(target.link, flush=True)
                    print(
                        "{} {}: {}".format(self.provider, target.name, "In Stock"),
                        flush=True,
                    )
                else:
                    print(
                        "{} {}: {}".format(self.provider, target.name, "Out of Stock"),
                        flush=True,
                    )
            except:
                print("Error fetching {} from {}".format(target.name, self.provider))
        return

    async def check_gpu(self, target):
        return

    async def main(self):
        start_time = datetime.datetime.now()
        await self.initialize()
        trials = 0
        while True:
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
        converted = remove_colors(Image.open(self.path + target.path), colors=colors_to_rid, replacement=(255,255,255))
        text = pytesseract.image_to_string(converted).strip()
        if text == "":
            self.check_gpu(target)
        else:
            if "sold out" in text.lower():
                return False
            else:
                return await self.validate(target)


class BandHScraper(GPUScraper):
    def __init__(self, interval, targets):
        super().__init__(interval, targets)
        self.path = "img/bandh/"
        self.provider = "B&H"

    async def validate(self, target):
        bandh_blue = (10, 146, 202)
        image = Image.open(self.path + target.path)
        return contains_color(image, colors=[bandh_blue])
        
        

    async def check_gpu(self, target):
        driver = self.driver
        driver.get(target.link)
        button = driver.find_element_by_class_name("cartRow_2dS2mdogHYAqhmKoANr6Ol")
        button.screenshot(self.path + target.path)
        await wait_one_second()
        button.screenshot(self.path + target.path)
        text = pytesseract.image_to_string(Image.open(self.path+target.path)).strip()
        if "notify" or "cart" in text.lower():
            if "add to cart" in text.lower():
                return await self.validate(target)
            else: return False
        
            




if __name__ == "__main__":

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
        gpu = GPU(**target)
        if "newegg" in gpu.link:
            newegg.append(gpu)
        elif "bhphotovideo" in gpu.link:
            b_and_h.append(gpu)
        elif "bestbuy" in gpu.link:
            best_buy.append(gpu)

    

    scraper = BBScraper(interval=wait_interval, targets=best_buy)
    # scraper = BandHScraper(interval=wait_interval, targets=b_and_h)
    asyncio.run(scraper.main())
