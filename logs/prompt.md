# 📄 Prompt Documentation – Book Description Enrichment Pipeline

This document contains the prompts and answers used to explain the data enrichment strategy applied in the Book Description Enrichment Pipeline project.

---

## 🟢 Prompt 1  
### From which sources did you fetch book descriptions if the library data (`library.csv`) already exists?

**Answer:**
- The base library dataset already contained book metadata but no descriptions  
- Descriptions were fetched from **OpenLibrary API** using ISBN  
- **Google Books** was used as a secondary source  
  - HTML scraping using ISBN  
  - Google Books API as fallback  
- For remaining missing cases, descriptions were fetched using **Title + Author** search on Google Books  

---

## 🟢 Prompt 2  
### How can book descriptions be scraped using OpenLibrary?

**Answer:**

There are **two ways** to fetch book descriptions from OpenLibrary:

---

### 1️⃣ Using OpenLibrary API (Preferred Method)

- Use the OpenLibrary Books API with ISBN as input  
- Endpoint example:  
/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data

- Extract the `description` field from the JSON response  
- Fast and reliable  
- Structured data (no HTML parsing required)  
- Suitable for large-scale processing  

**Limitations:**
- Many Indian publications return `"Not Found"`  
- Some books do not have descriptions available via API  

---

### 2️⃣ Using HTML Scraping (BeautifulSoup)

- Access the OpenLibrary book detail page using ISBN or work ID  
- Parse HTML content using **BeautifulSoup**  
- Extract description text from relevant HTML tags  
- Used when API does not return a description  

**Benefits of HTML Scraping:**
- Allows cross-verification with original webpage content  
- Some descriptions exist on the webpage but not in the API  
- Useful as a fallback strategy  

---

## 🟢 Prompt 3  
### Can we first scrape from Google Books and then OpenLibrary and cross-verify both?

**Answer:**

Yes, the data enrichment process can be designed using a **cross-verification strategy** as follows:

---

### 1️⃣ Primary Source – Google Books

- Fetch or scrape book descriptions from **Google Books**  
- Methods used:
- HTML scraping using ISBN  
- API fallback when available  
- Reason:
- Better coverage for Indian and international publications  
- Richer and more detailed descriptions  

---

### 2️⃣ Secondary Source – OpenLibrary

- Fetch descriptions using **OpenLibrary API** or HTML pages  
- Used as a **verification and fallback source**  
- Helps validate the authenticity of descriptions  

---

### 3️⃣ Cross-Verification Logic

- If description is found in **both sources**:
- Compare length and content similarity  
- Prefer the more detailed or non-null description  
- If description exists in **only one source**:
- Accept the available description  
- If descriptions mismatch:
- Give priority to Google Books (higher coverage)  
- Use OpenLibrary for validation  

---

## 🟢 Prompt 4  
### What do you do if book descriptions are still not found after Google Books and OpenLibrary?

**Answer:**

---

### 🔁 Final Fallback – Title + Author Based Fetch

- Identify records where description is still `"Not Found"` or null  
- Ignore ISBN for these records  
- Use **Title + Author** as the search query  

---

### 🔍 Search Strategy

- Clean title and author text:
- Convert to lowercase  
- Remove punctuation and extra spaces  
- Send query to **Google Books search endpoint**  
- Fetch the most relevant matching result  

---

### 📝 Description Extraction

- Extract description from:
- Google Books API response, or  
- Google Books HTML page (if API fails)  
- Validate that the returned book matches the given title and author  

---

### ✅ Why Title + Author Works

- Many books have:
- Missing ISBN  
- Incorrect ISBN  
- Local or Indian editions without ISBN  
- Title + Author provides semantic matching  
- Increases description recovery rate  

---
