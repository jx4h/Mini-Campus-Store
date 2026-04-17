// ================= CART (FLASK SESSION) =================

// ---------- OPEN / CLOSE PANELS ----------
function openCart() {
    document.getElementById("overlay").style.display = "block";
    document.getElementById("cartPanel").classList.add("active");
    loadCartWidget();
  }
  
  function openWishlist() {
    document.getElementById("overlay").style.display = "block";
    document.getElementById("wishlistPanel").classList.add("active");
  }
  
  function closePanels() {
    document.getElementById("overlay").style.display = "none";
    document.querySelectorAll(".side-panel").forEach(p =>
      p.classList.remove("active")
    );
  }
  
  // ---------- LOAD CART WIDGET ----------
  function loadCartWidget() {
    fetch("/cart")
      .then(res => res.text())
      .then(html => {
        const temp = document.createElement("div");
        temp.innerHTML = html;
        const body = temp.querySelector("body");
        document.getElementById("cartContent").innerHTML =
          body ? body.innerHTML : "<p>Cart empty</p>";
      });
  }
  
  // ---------- ADD TO CART ----------
  function addToCart(productId) {
    fetch(`/cart/add/${productId}`, { method: "POST" })
      .then(res => res.json())
      .then(() => {
        const countEl = document.getElementById("cart-count");
        if (countEl) {
          countEl.textContent = parseInt(countEl.textContent) + 1;
        }
      });
  }
  
  // ---------- CHANGE QUANTITY ----------
  function changeQty(productId, delta) {
    const item = document.querySelector(`[data-id="${productId}"]`);
    let qty = parseInt(item.dataset.qty) + delta;
    if (qty < 0) qty = 0;
  
    fetch("/cart/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: productId,
        quantity: qty
      })
    }).then(() => loadCartWidget());
  }
  
  // ---------- REMOVE ITEM ----------
  function removeItem(productId) {
    fetch(`/cart/remove/${productId}`, { method: "POST" })
      .then(() => loadCartWidget());
  }
  function moveToCart(productId) {
    fetch(`/cart/add/${productId}`, { method: "POST" })
      .then(res => res.json())
      .then(data => {
        document.getElementById("cart-count").textContent = data.count;
        // remove from wishlist
        fetch(`/wishlist/toggle/${productId}`, { method: "POST" })
          .then(res => res.json())
          .then(wish => {
            document.getElementById("wishlist-count").textContent = wish.count;
            loadWishlistPanel(); // reload mini-panel
          });
      });
  }