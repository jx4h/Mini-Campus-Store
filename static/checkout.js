document.addEventListener("DOMContentLoaded", async () => {
    const stripe = Stripe(document.getElementById("pay-btn").dataset.key);
    const cardElement = document.getElementById("card-element");
    const payBtn = document.getElementById("pay-btn");
    const paymentMessage = document.getElementById("payment-message");

    // إنشاء Stripe Elements
    const elements = stripe.elements();
    const card = elements.create("card");
    card.mount(cardElement);

    payBtn.addEventListener("click", async () => {
        // جلب clientSecret من السيرفر
        const res = await fetch("/create-payment-intent", { method: "POST" });
        const data = await res.json();
        const clientSecret = data.clientSecret;

        // تأكيد الدفع
        const { paymentIntent, error } = await stripe.confirmCardPayment(clientSecret, {
            payment_method: {
                card: card,
                billing_details: {
                    name: document.getElementById("name").value,
                    email: document.getElementById("email").value
                }
            }
        });

        if (error) {
            paymentMessage.textContent = error.message;
            payBtn.disabled = false;
        } else if (paymentIntent.status === "succeeded") {
            paymentMessage.textContent = "Payment Successful!";
            // مسح الكارت بعد الدفع
            localStorage.removeItem("cart");
            localStorage.removeItem("cart_total");
            window.location.href = "/payment-success";
        }
    });
});