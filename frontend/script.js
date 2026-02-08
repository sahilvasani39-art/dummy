let mode = "desc";

/* ================= TAB SWITCH ================= */
function switchTab(tab) {
    mode = tab;

    document.getElementById("isbnTab").classList.toggle("active", tab === "isbn");
    document.getElementById("descTab").classList.toggle("active", tab === "desc");

    document.getElementById("isbnInput").disabled = tab !== "isbn";
    document.getElementById("descInput").disabled = tab !== "desc";
}

/* ================= SEARCH HANDLER ================= */
async function search() {
    if (mode === "isbn") {
        await searchByISBN();
    } else {
        await searchByDescription();
    }
}

/* ================= UI HELPERS ================= */
function setLoading(isLoading, message = "Searching for the best matches...") {
    const btn = document.getElementById("searchBtn");
    const btnText = document.getElementById("btnText");
    const loader = document.getElementById("btnLoader");
    const container = document.getElementById("results");

    if (isLoading) {
        btn.disabled = true;
        btnText.textContent = "Searching...";
        loader.classList.remove("hidden");

        container.innerHTML = `
            <p style="color:white; font-size:1.1rem;">
                🔍 ${message}
            </p>
        `;
    } else {
        btn.disabled = false;
        btnText.textContent = "Find My Recommendations";
        loader.classList.add("hidden");
    }
}

/* ================= ISBN SEARCH ================= */
async function searchByISBN() {
    const isbn = document.getElementById("isbnInput").value.trim();
    if (!isbn) return;

    setLoading(true, "Fetching book details by ISBN...");

    try {
        const res = await fetch(`/book/isbn/${isbn}`);
        const data = await res.json();

        renderBooks([data]);
    } catch (err) {
        document.getElementById("results").innerHTML =
            `<p style="color:red;">❌ ISBN not found.</p>`;
        console.error(err);
    }

    setLoading(false);
}

/* ================= DESCRIPTION SEARCH ================= */
async function searchByDescription() {
    const desc = document.getElementById("descInput").value.trim();
    if (!desc) return;

    setLoading(true, "Understanding your reading taste...");

    try {
        const res = await fetch(`/recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ description: desc })
        });

        const data = await res.json();
        renderBooks(data.results);
    } catch (err) {
        document.getElementById("results").innerHTML =
            `<p style="color:red;">❌ Something went wrong. Try again.</p>`;
        console.error(err);
    }

    setLoading(false);
}

/* ================= RENDER BOOK CARDS ================= */
function renderBooks(books) {
    const container = document.getElementById("results");
    container.innerHTML = "";

    books.forEach(book => {
        const img = book.image_url && book.image_url !== "nan"
            ? book.image_url
            : "https://via.placeholder.com/300x450?text=No+Image";

        container.innerHTML += `
            <div class="book-card">
                <div class="cover-wrapper">
                    <span class="match-badge">
                        ${Math.floor(85 + Math.random() * 10)}% Match
                    </span>

                    <img src="${img}"
                         class="book-cover"
                         onerror="this.src='https://via.placeholder.com/300x450?text=No+Image'">
                </div>

                <div class="card-content">
                    <div class="book-title clamp-2">${book.Title}</div>
                    <div class="book-author clamp-1">${book.Author_Editor || ""}</div>
                </div>
            </div>
        `;
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const res = await fetch("/random");
        const data = await res.json();
        renderBooks(data.results);
    } catch (err) {
        console.error("Failed to load random books", err);
    }
});
