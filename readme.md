----------------------------
Prerequisites / Dependencies
----------------------------
Use "pip install <package>" for all of the below:
    - pillow
    - pytesseract
    - selenium
    - playsound

*Selenium requires a browser driver if you're on windows you're covered... if you're on another platform please
"google selenium webdriver <your_os_here>" and place it in this directory. You will then have to modify line 43 of "gpu_scraper.py"

The scraper requires Tesseract-OCR to be installed
    - Windows: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.0.0-alpha.20201127.exe
        - If you're running 64 bit it should already be pointed to the right location on lines 10-12 of "gpu_scraper.py"
    - See this for mac installation: https://guides.library.illinois.edu/c.php?g=347520&p=4121425
        - You will also have to point pytesseract to this on lines 10-12 of "gpu_scraper.py"


----------------------------
Configuration
----------------------------
"gpu_scraper.json" can be modified to check stock on any item sold by best buy. Simply follow the same
format for inputting the name and link of the item (DO NOT USE SPECIAL CHARACTERS OR SPACES IN NAME FIELD).

You can also set the sleep interval after each iteration of requests (unit is seconds)

----------------------------
To Run Scraper:
1) Open terminal in this directory
2) run "python gpu_scraper.py"
3) Wait...