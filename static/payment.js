// 🔹 Replace with your own publishable key
const stripe = Stripe("mk_1SgB7zB2kDAcQnZ2u7pvjX9f"); 

const elements = stripe.elements();
const card = elements.create("card");
card.mount("#card-element");

const payBtn = document.getElementById("pay-btn");
const message = document.getElementById("payment-message");
const totalSpan = document.getElementById("total-amount");

// قراءة المبلغ الحقيقي من الكارت
const cart = JSON.parse(localStorage.getItem("cart")) || [];

let totalAmount = 0;
cart.forEach(item => {
  totalAmount += item.price * item.quantity;
});

// tax logic (same as cart)
const tax = totalAmount > 500 ? 0 : totalAmount * 0.10;
totalAmount += tax;

totalSpan.textContent = totalAmount.toFixed(2);

payBtn.addEventListener("click", async (e) => {
    e.preventDefault();

    if (!totalAmount || totalAmount <= 0) {
        message.style.color = "red";
        message.textContent = "Invalid amount";
        return;
    }

    message.style.color = "black";
    message.textContent = "Processing payment...";

    // إنشاء PaymentIntent من السيرفر
    const response = await fetch("http://localhost:3000/create-payment-intent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            amount: Math.round(totalAmount * 100) // تحويل لجنيهات لملي
        })
    });

    const data = await response.json();

    const result = await stripe.confirmCardPayment(data.clientSecret, {
        payment_method: { card: card }
    });

    if (result.error) {
        message.style.color = "red";
        message.textContent = result.error.message;
    } else {
        if (result.paymentIntent.status === "succeeded") {
            message.style.color = "green";
            message.textContent = "Payment Successful!";

            // تفريغ الكارت بعد نجاح الدفع
            localStorage.removeItem("cart");
            localStorage.removeItem("cart_total");

            setTimeout(() => {
                window.location.href = "success.html";
            }, 2000);
        }
    }
});