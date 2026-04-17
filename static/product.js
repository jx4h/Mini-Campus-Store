console.log("product.js loaded");

// المنتجات الافتراضية
const defaultProducts = [
    { name: "Wireless Earbuds", price: 300, image: "Image20250515193226.jpg", category: "electronics" },
    { name: "Graphic T-Shirt", price: 150, image: "Image20250515192642.jpg", category: "fashion" },
    { name: "Coffee Mug", price: 90, image: "Image20250515192645.jpg", category: "home" }
];

// دالة لإضافة منتج للكارت
function addToCart(name, price) {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];
    let existing = cart.find(item => item.name === name);

    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ name: name, price: price, quantity: 1 });
    }

    localStorage.setItem("cart", JSON.stringify(cart));
    updateCartCount();
}

// تحديث عداد الكارت
function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem("cart")) || [];
    const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);
    const cartCountSpan = document.getElementById("cart-count");
    if (cartCountSpan) {
        cartCountSpan.textContent = totalQuantity;
    }
}

// عرض كل المنتجات
function displayProducts() {
    const container = document.getElementById("productsContainer");
    if (!container) return;

    // جلب المنتجات المضافة من المستخدم
    const userProducts = JSON.parse(localStorage.getItem("userProducts")) || [];

    // دمج كل المنتجات
    const allProducts = [...defaultProducts, ...userProducts];

    container.innerHTML = "";

    allProducts.forEach(product => {
        const div = document.createElement("div");
        div.className = "product";
        div.setAttribute("data-category", product.category || "other");

        div.innerHTML = `
            <img src="${product.image}" alt="${product.name}">
            <h3>${product.name}</h3>
            <p>Price: EGP ${product.price}</p>
            <button class="add-to-cart-btn">Add to Cart</button>
        `;

        container.appendChild(div);
    });

    // ربط أزرار Add to Cart
    document.querySelectorAll(".add-to-cart-btn").forEach(button => {
        button.addEventListener("click", () => {
            const productDiv = button.closest(".product");
            const name = productDiv.querySelector("h3").innerText;
            const priceText = productDiv.querySelector("p").innerText;
            const price = parseFloat(priceText.replace("Price: EGP ", ""));
            addToCart(name, price);
        });
    });
}

// البحث عن المنتجات
function searchProducts() {
    const input = document.getElementById('searchInput').value.toLowerCase();
    const products = document.getElementsByClassName('product');

    for (let i = 0; i < products.length; i++) {
        const productName = products[i].getElementsByTagName('h3')[0].innerText.toLowerCase();
        products[i].style.display = productName.includes(input) ? '' : 'none';
    }
}

// الفلترة حسب الفئة
function filterByCategory() {
    const selectedCategory = document.getElementById('categoryFilter').value;
    const products = document.getElementsByClassName('product');

    for (let i = 0; i < products.length; i++) {
        const category = products[i].getAttribute('data-category');
        products[i].style.display = (selectedCategory === 'all' || category === selectedCategory) ? '' : 'none';
    }
}

// تحميل المنتجات وعداد الكارت عند فتح الصفحة
document.addEventListener("DOMContentLoaded", () => {
    displayProducts();
    updateCartCount();
});