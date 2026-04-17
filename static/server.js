// ================== IMPORTS ==================
const express = require("express");
const stripe = require("stripe")("mk_1SgB8eB2kDAcQnZ2ggojoIsj"); // 🔴 حطي Secret Key هنا
const cors = require("cors");

// ================== APP SETUP ==================
const app = express();

app.use(cors());
app.use(express.json());

// ================== CREATE PAYMENT INTENT ==================
app.post("/create-payment-intent", async (req, res) => {
    try {
        const { amount } = req.body;

        if (!amount) {
            return res.status(400).json({ error: "Amount is required" });
        }

        const paymentIntent = await stripe.paymentIntents.create({
            amount: amount,          // بالملي (مثال: 50000 = 500 جنيه)
            currency: "egp",
            payment_method_types: ["card"],
        });

        res.json({
            clientSecret: paymentIntent.client_secret,
        });

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: error.message });
    }
});

// ================== SERVER START ==================
app.listen(3000, () => {
    console.log("✅ Server running on http://localhost:3000");
});