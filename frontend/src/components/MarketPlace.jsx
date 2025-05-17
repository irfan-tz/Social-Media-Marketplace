import React, { useState, useEffect } from "react";
import "../assets/styles/MarketPlace.css";

function Marketplace() {
    const [showPayment, setShowPayment] = useState(false);
    const [selectedItem, setSelectedItem] = useState(null);
    const [cardDetails, setCardDetails] = useState({
        number: "",
        expiry: "",
        cvv: "",
    });
    const [processing, setProcessing] = useState(false);
    const [paymentStatus, setPaymentStatus] = useState(null);

    // Format price with commas and 2 decimal places
    const formatPrice = (price) => {
        return price.toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    };

    // Sample marketplace items
    const items = [
        {
            id: 1,
            title: "Vintage Camera",
            price: 59999.99,
            image: "https://images.unsplash.com/photo-1508185644026-3759baed1f69",
            seller: "John Doe",
            description:
                "Excellent condition vintage Canon camera with original leather case.",
        },
        {
            id: 2,
            title: "PS4 - Dave2D edition",
            price: 49690,
            image: "https://images.unsplash.com/photo-1486401899868-0e435ed85128",
            seller: "Jane Smith",
            description: "Sony PS4 (Dave2D edition) with controller.",
        },
        {
            id: 3,
            title: "Sony WH-1000XM5",
            price: 29999.99,
            image: "https://highxtar.com/wp-content/uploads/2023/06/IMG_5175.jpg.webp",
            seller: "Bob Wilson",
            description:
                "Sony's WH-1000XM5 wireless headphones with noise cancellation, superior sound and call quality.",
        },
        {
            id: 4,
            title: "Alexandar The Great's Mummy (preserved)",
            price: 32335600.0,
            image: "https://egypttourz.com/wp-content/uploads/2023/03/Ancient-Egyptian-Sarcophagi.jpg.webp",
            seller: "Alice Brown",
            description:
                "Mummy of Alexander the Great in mind condition, just like new!",
        },
    ];

    const handleBuyNow = (item) => {
        setSelectedItem(item);
        setShowPayment(true);
        setPaymentStatus(null);
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setCardDetails((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const formatCardNumber = (value) => {
        return value
            .replace(/\D/g, "")
            .replace(/(\d{4})(?=\d)/g, "$1 ")
            .substring(0, 19);
    };

    const handlePayment = async (e) => {
        e.preventDefault();
        setProcessing(true);

        try {
            // Clean and validate data
            const cleanedCard = cardDetails.number.replace(/\D/g, "");
            let cleanedExpiry = cardDetails.expiry.replace(/\D/g, ""); // Remove all non-digits

            // Ensure MMYY format (frontend shows MM/YY but sends MMYY)
            if (cleanedExpiry.length > 2) {
                cleanedExpiry =
                    cleanedExpiry.slice(0, 2) + cleanedExpiry.slice(2, 4);
            }

            const cleanedCVV = cardDetails.cvv.replace(/\D/g, "");

            // Validation
            const errors = [];
            if (cleanedCard.length < 15 || cleanedCard.length > 16) {
                errors.push("Card number must be 15-16 digits");
            }
            if (cleanedExpiry.length !== 4) {
                errors.push("Expiry must be MM/YY format");
            }
            if (cleanedCVV.length < 3) {
                errors.push("CVV must be 3 digits");
            }

            if (errors.length > 0) {
                throw new Error(errors.join("\n"));
            }

            const response = await fetch("/api/payments/process/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
                body: JSON.stringify({
                    card_number: cleanedCard,
                    expiry: cleanedExpiry, // Now sending MMYY without slash
                    cvv: cleanedCVV,
                    amount: selectedItem.price.toFixed(2),
                }),
            });

            const data = await response.json();

            if (response.ok && data.status === "success") {
                setPaymentStatus("success");
                setTimeout(() => {
                    setShowPayment(false);
                    setProcessing(false);
                }, 5000); // Increased from 3000 to 5000 ms
            } else {
                throw new Error(data.error || "Payment failed");
            }
        } catch (error) {
            console.error("Payment error:", error);
            setPaymentStatus("failed");
            alert(error.message);
            setProcessing(false);
        }
    };

    return (
        <div className="marketplace-container fade-in">
            <h1>Marketplace</h1>

            <div className="marketplace-filters slide-up">
                <input
                    type="text"
                    placeholder="Search items..."
                    className="search-input"
                />
                <select className="filter-select">
                    <option value="">All Categories</option>
                    <option value="electronics">Electronics</option>
                    <option value="clothing">Clothing</option>
                    <option value="books">Books</option>
                    <option value="other">Other</option>
                </select>
                <button className="btn-primary">Post Item</button>
            </div>

            <div className="items-grid">
                {items.map((item) => (
                    <div key={item.id} className="item-card slide-up">
                        <img
                            src={item.image}
                            alt={item.title}
                            className="item-image"
                        />
                        <div className="item-details">
                            <h3>{item.title}</h3>
                            <p className="item-price">
                                ₹{formatPrice(item.price)}
                            </p>
                            <p className="item-seller">Seller: {item.seller}</p>
                            <p className="item-description">
                                {item.description}
                            </p>
                            <div className="item-actions">
                                <button
                                    className="btn-primary"
                                    onClick={() => handleBuyNow(item)}
                                >
                                    Buy Now
                                </button>
                                <button className="btn-secondary">
                                    Message Seller
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {showPayment && (
                <div className="payment-modal">
                    <div className="payment-content slide-up">
                        <h2>Complete Purchase</h2>
                        <div className="payment-details">
                            <h3>{selectedItem.title}</h3>
                            <p className="price">
                                Total: ₹{formatPrice(selectedItem.price)}
                            </p>
                        </div>

                        {!paymentStatus ? (
                            <form
                                onSubmit={handlePayment}
                                className="payment-form"
                            >
                                <div className="form-group">
                                    <label>Card Number</label>
                                    <input
                                        type="text"
                                        name="number"
                                        placeholder="4242 4242 4242 4242"
                                        value={formatCardNumber(
                                            cardDetails.number,
                                        )}
                                        onChange={(e) =>
                                            handleInputChange({
                                                target: {
                                                    name: "number",
                                                    value: e.target.value.replace(
                                                        /\D/g,
                                                        "",
                                                    ),
                                                },
                                            })
                                        }
                                        maxLength="19"
                                    />
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Expiry Date (MM/YY)</label>
                                        <input
                                            type="text"
                                            name="expiry"
                                            placeholder="MM/YY"
                                            value={cardDetails.expiry}
                                            onChange={(e) => {
                                                let value =
                                                    e.target.value.replace(
                                                        /\D/g,
                                                        "",
                                                    );
                                                if (value.length > 2) {
                                                    value = `${value.slice(0, 2)}/${value.slice(2, 4)}`;
                                                }
                                                handleInputChange({
                                                    target: {
                                                        name: "expiry",
                                                        value,
                                                    },
                                                });
                                            }}
                                            maxLength="5"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>CVV</label>
                                        <input
                                            type="text"
                                            name="cvv"
                                            placeholder="123"
                                            value={cardDetails.cvv}
                                            onChange={handleInputChange}
                                            maxLength="3"
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    className="btn-primary"
                                    disabled={
                                        processing ||
                                        !cardDetails.number ||
                                        !cardDetails.expiry ||
                                        !cardDetails.cvv
                                    }
                                >
                                    {processing
                                        ? "Processing..."
                                        : `Pay ₹${formatPrice(selectedItem.price)}`}
                                </button>
                            </form>
                        ) : (
                            <div className={`payment-status ${paymentStatus}`}>
                                {paymentStatus === "success" ? (
                                    <>
                                        <div className="success-icon">✓</div>
                                        <h3>Payment Successful!</h3>
                                        <p>Thank you for your purchase</p>
                                    </>
                                ) : (
                                    <>
                                        <div className="error-icon">✕</div>
                                        <h3>Payment Failed</h3>
                                        <p>Please try again</p>
                                    </>
                                )}
                            </div>
                        )}

                        <button
                            className="btn-secondary close-button"
                            onClick={() => {
                                setShowPayment(false);
                                setPaymentStatus(null);
                                setCardDetails({
                                    number: "",
                                    expiry: "",
                                    cvv: "",
                                });
                            }}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Marketplace;
