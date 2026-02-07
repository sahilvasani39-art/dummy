let mode = "desc";

// Tab switch
function switchTab(tab) {
    mode = tab;

    document.getElementById("isbnTab").classList.toggle("active", tab === "isbn");
    document.getElementById("descTab").classList.toggle("active", tab === "desc");

    document.getElementById("isbnInput").disabled = tab !== "isbn";
    document.getElementById("descInput").disabled = tab !== "desc";
}

// Search handler
async function search() {
    if (mode === "isbn") {
        searchByISBN();
    } else {
        searchByDescription();
    }
}

// ISBN
async function searchByISBN() {
    const isbn = document.getElementById("isbnInput").value;
    const res = await fetch(`/book/isbn/${isbn}`);
    const data = await res.json();
    renderBooks([data]);
}

// DESCRIPTION
async function searchByDescription() {
    const desc = document.getElementById("descInput").value;

    const res = await fetch(`/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: desc })
    });

    const data = await res.json();
    renderBooks(data.results);
}

// Render cards
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
    const res = await fetch("/random");
    const data = await res.json();
    renderBooks(data.results);
});
