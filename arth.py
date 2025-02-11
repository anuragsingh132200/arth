import requests
import csv
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Define the range of loop numbers
start_num = 905527
end_num = 905651

# CSV file to store data
csv_filename = "kautilya_arthashastra_translations1.csv"

# Define headers to mimic browser requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Function to fetch word translations sequentially
def get_word_translations(word):
    url = f"https://www.wisdomlib.org/sanskrit/segments/{word}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            translation_section = soup.find_all("p")
            if len(translation_section) > 4:
                text = translation_section[4].text
                translations = {lang: "" for lang in ["Devanagari/Hindi", "Bengali", "Gujarati", "Kannada", "Malayalam", "Telugu"]}
                for lang in translations.keys():
                    if f"[{lang}]" in text:
                        start = text.find(f"[{lang}]") + len(f"[{lang}] ")
                        end = text.find(",", start) if "," in text[start:] else len(text)
                        translations[lang] = text[start:end].strip()
                return translations
    except Exception as e:
        print(f"Error fetching translation for {word}: {e}")
    return None

# Function to fetch and process a single URL
def fetch_and_process_url(num):
    url = f"https://www.wisdomlib.org/hinduism/book/kautilya-arthashastra-sanskrit/d/doc{num}.html"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.find("h1", class_="h2 pt-2")
            title = title.text.strip() if title else "N/A"

            kaz_div = soup.find("div", class_="col-12 mt-3 mb-5 chapter-content text_1730 sanskrit-default")
            if kaz_div and kaz_div.text.startswith("[English text for this chapter is available]"):
                kaz_div.string = kaz_div.text.replace("[English text for this chapter is available]", "")

            if kaz_div:
                kaz_paragraphs = kaz_div.find_all("p")
                for p in kaz_paragraphs:
                    kaz_content = p.text.strip()
                    if kaz_content:
                        if(kaz_content=="[English text for this chapter is available]"):
                            continue
                        words = kaz_content.split()
                        translations = {lang: "" for lang in ["Devanagari/Hindi", "Bengali", "Gujarati", "Kannada", "Malayalam", "Telugu"]}
                        words = [w for w in words if w != "[English text for this chapter is available]"]                        # Fetch translations sequentially
                        for word in words:
                            if word in ["[English", "text", "for", "this", "chapter", "is", "available]"]:
                                continue
                            result = get_word_translations(word)
                            if result:
                                for lang in translations.keys():
                                    translations[lang] += result[lang] + " "

                        return [
                            title, kaz_content,
                            translations["Devanagari/Hindi"].strip(),
                            translations["Bengali"].strip(),
                            translations["Gujarati"].strip(),
                            translations["Kannada"].strip(),
                            translations["Malayalam"].strip(),
                            translations["Telugu"].strip()
                        ]
        print(f"Scraped: {url}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

# Open CSV file for writing
with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Title", "KAZ index", "Sanskrit", "Devanagari/Hindi", "Bengali", "Gujarati", "Kannada", "Malayalam", "Telugu"])

    # Use ThreadPoolExecutor to fetch URLs concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_and_process_url, num) for num in range(start_num, end_num + 1)]
        for future in as_completed(futures):
            result = future.result()
            if result:
                csv_writer.writerow(result)

print("Scraping completed! Data saved in", csv_filename)