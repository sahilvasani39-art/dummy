import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote_plus

INPUT_CSV = r"D:\\COLLAGE\\DAIICT\\2 - SEM\\BDE\\Project\\Big-Data-Engineering-\\Data\\raw_data\\dau_library_data.csv"
FINAL_OUTPUT = "dau_with_description.csv"

MISSING_VALUES = ["Not Found", "ISBN Not Matched", "Description Not Available"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Sahil-BookBot/1.0)"
}


def clean_isbn(isbn):
    return re.sub(r"[^0-9Xx]", "", str(isbn))

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def load_library_data():
    columns = [
        "Acc_Date", "Acc_No", "Title", "ISBN", "Author_Editor",
        "Edition_Volume", "Place_Publisher", "Year", "Pages", "Class_No"
    ]
    df = pd.read_csv(
        INPUT_CSV,
        usecols=range(len(columns)),
        names=columns,
        header=0,
        dtype={"ISBN": str},
        encoding="latin1"
    )
    df = df.drop_duplicates(subset=["ISBN"])

    df["description"] = "Not Found"
    df["image_url"] = "Not Available"
    df["book_url"] = "Not Available"

    return df


from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_openlibrary_descriptions(df, max_workers=30, delay=0.1):
    df = df.copy()
    df["description"] = "ISBN Not Matched"
    lock = threading.Lock()

    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=max_workers, pool_maxsize=max_workers)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    def fetch_description(row_index, isbn):
        desc = "ISBN Not Matched"
        img_url = "Not Available"
        book_url = "Not Available"

        isbn_clean = clean_isbn(isbn)

        if isbn_clean:
            try:
                url = f"https://openlibrary.org/isbn/{isbn_clean}"
                r = session.get(url, headers=HEADERS, timeout=10)

                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    p = soup.select_one("div.book-description div.read-more__content p")
                    desc = p.get_text(strip=True) if p else "Description Not Available"

                    # ✅ ONLY IF description found
                    if desc not in MISSING_VALUES:
                        img_url = f"https://covers.openlibrary.org/b/isbn/{isbn_clean}-L.jpg"
                        book_url = url
            except:
                pass

        time.sleep(delay)
        with lock:
            df.at[row_index, "description"] = desc
            df.at[row_index, "image_url"] = img_url
            df.at[row_index, "book_url"] = book_url

    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, row in df.iterrows():
            futures.append(executor.submit(fetch_description, i, row["ISBN"]))

        for _ in tqdm(as_completed(futures), total=len(futures), desc="OpenLibrary"):
            pass

    return df




from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def fetch_google_html_descriptions(df, max_workers=10, delay=0.1):
    df = df.copy()
    lock = threading.Lock()
    session = requests.Session()

    def fetch_description(row_index, isbn):
        desc = df.at[row_index, "description"]
        img_url = df.at[row_index, "image_url"]
        book_url = df.at[row_index, "book_url"]

        isbn_clean = clean_isbn(isbn)

        if isbn_clean:
            try:
                url = f"https://books.google.com/books?vid=ISBN{isbn_clean}"
                r = session.get(url, headers=HEADERS, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                div = soup.find("div", id="synopsis")

                if div:
                    desc = div.get_text(separator=" ", strip=True)

                    # ✅ ONLY IF description found
                    if desc not in MISSING_VALUES:
                        book_url = url
                        img_url = f"https://covers.openlibrary.org/b/isbn/{isbn_clean}-L.jpg"
            except:
                pass

        time.sleep(delay)
        with lock:
            df.at[row_index, "description"] = desc
            df.at[row_index, "image_url"] = img_url
            df.at[row_index, "book_url"] = book_url

    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, row in df.iterrows():
            if df.at[i, "description"] in MISSING_VALUES:
                futures.append(executor.submit(fetch_description, i, row["ISBN"]))

        for _ in tqdm(as_completed(futures), total=len(futures), desc="Google HTML"):
            pass

    return df


def google_books_api_search(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1"
    try:
        res = requests.get(url, timeout=10).json()
        items = res.get("items")
        if not items:
            return None
        return items[0].get("volumeInfo", {}).get("description")
    except:
        return None

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def fetch_google_api_fallback(df, max_workers=10, delay=0.1):
    df = df.copy()
    df["clean_title"] = df["Title"].apply(clean_text)
    df["clean_author"] = df["Author_Editor"].apply(clean_text)

    lock = threading.Lock()
    session = requests.Session()

    def fetch_description(row_index, title, author):
        desc = df.at[row_index, "description"]
        img_url = df.at[row_index, "image_url"]
        book_url = df.at[row_index, "book_url"]

        queries = [ 
            f"intitle:{title}+inauthor:{author}",
            f"intitle:{title}"
        ]

        for q in queries:
            try:
                url = f"https://www.googleapis.com/books/v1/volumes?q={quote_plus(q)}&maxResults=1"
                res = session.get(url, timeout=10).json()
                items = res.get("items")

                if items:
                    result = items[0].get("volumeInfo", {}).get("description")
                    if result and len(result) > 50:
                        desc = result

                        # ✅ ONLY IF description found
                        isbn = clean_isbn(df.at[row_index, "ISBN"])
                        if isbn:
                            img_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
                            book_url = f"https://books.google.com/books?vid=ISBN{isbn}"
                        break
            except:
                pass

        time.sleep(delay)
        with lock:
            df.at[row_index, "description"] = desc
            df.at[row_index, "image_url"] = img_url
            df.at[row_index, "book_url"] = book_url

    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, row in df.iterrows():
            if row["description"] in MISSING_VALUES:
                futures.append(executor.submit(fetch_description, i, row["clean_title"], row["clean_author"]))

        for _ in tqdm(as_completed(futures), total=len(futures), desc="Google API"):
            pass

    return df.drop(columns=["clean_title", "clean_author"])


def copy_isbn(df1,df4):
  df_lib=df1.copy()
  df_desc =df4.copy()

  match_cols = ["Title", "Author_Editor", "Edition_Volume", "Place_Publisher", "Year"]

  def clean_text_for_match(text):
      text = str(text).lower().strip()
      text = re.sub(r"[^\w\s]", "", text)
      text = re.sub(r"\s+", " ", text)
      return text

  for col in match_cols:
      df_lib[col + "_clean"] = df_lib[col].apply(clean_text_for_match)
      df_desc[col + "_clean"] = df_desc[col].apply(clean_text_for_match)

  isbn_map = df_lib.set_index([col + "_clean" for col in match_cols])["ISBN"].to_dict()

  def get_isbn(row):
      key = tuple(row[col + "_clean"] for col in match_cols)
      return isbn_map.get(key, row["ISBN"])

  df_desc["ISBN"] = df_desc.apply(get_isbn, axis=1)

  df_desc.drop(columns=[col + "_clean" for col in match_cols], inplace=True)

  return df_desc

def cleaning(df):
  df = df[
      ((df["image_url"] != "Not Available") &
      (df["description"] != "ISBN Not Matched") &
      (df["book_url"] != "Not Available"))
  ]
  df = df[~
      (df["description"].isna())
  ].copy()

  return df


def run_pipeline():
    print("🔹 Loading base library data...")
    df1 = load_library_data()

    print("🔹 Fetching OpenLibrary descriptions...")
    df2 = fetch_openlibrary_descriptions(df1)

    print("🔹 Fetching Google Books HTML descriptions...")
    df3 = fetch_google_html_descriptions(df2)

    print("🔹 Fetching Google Books API fallback descriptions...")
    df4 = fetch_google_api_fallback(df3)

    print("🔹Copy ISBN...")
    df5 = copy_isbn(df1,df4)

    print("🔹Cleaning data...")
    df6 = copy_isbn(df5)

    print("🔹 Saving FINAL output...")
    df6.to_csv(FINAL_OUTPUT, index=False)

    print(f"\n✅ DONE Final file created: {FINAL_OUTPUT}")

if __name__ == "__main__":
    run_pipeline()
