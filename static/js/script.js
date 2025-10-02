// Password toggle functionality
document.addEventListener("DOMContentLoaded", function () {
  // Password toggle
  const toggleButtons = document.querySelectorAll(".password-toggle");
  toggleButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target");
      const passwordInput = document.getElementById(targetId);
      const icon = this.querySelector("i");

      if (passwordInput.type === "password") {
        passwordInput.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
      } else {
        passwordInput.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
      }
    });
  });

  // Auto-hide flash messages
  const flashMessages = document.querySelectorAll(".alert");
  flashMessages.forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });

  // Phone number formatting
  const phoneInput = document.getElementById("phone");
  if (phoneInput) {
    phoneInput.addEventListener("input", function (e) {
      let value = e.target.value.replace(/\D/g, "");
      if (!value.startsWith("91")) {
        value = "91" + value;
      }
      if (value.length > 2) {
        value = "+" + value.substring(0, 2) + " " + value.substring(2);
      }
      e.target.value = value;
    });
  }

  // OTP request handling
  const otpButtons = document.querySelectorAll(".send-otp-btn");
  otpButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const form = this.closest("form");
      const email = form.querySelector("#email")?.value;
      const phone = form.querySelector("#phone")?.value;
      const purpose = this.getAttribute("data-purpose");

      if (!email) {
        alert("Please enter email address!");
        return;
      }

      if (purpose === "register" && !phone) {
        alert("Please enter phone number!");
        return;
      }

      this.disabled = true;
      this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

      fetch(purpose === "register" ? "/send_register_otp" : "/send_reset_otp", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, phone }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            alert("OTP sent successfully!");
            // Enable OTP input field
            const otpInput = form.querySelector("#otp");
            if (otpInput) {
              otpInput.disabled = false;
              otpInput.focus();
            }
          } else {
            alert(data.message);
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("Failed to send OTP. Please try again.");
        })
        .finally(() => {
          this.disabled = false;
          this.innerHTML =
            purpose === "register" ? "Send OTP" : "Send Reset OTP";
        });
    });
  });

  // Cart quantity updates with real-time calculation
  initializeCartQuantityHandlers();

  // Print receipt
  const printButtons = document.querySelectorAll(".print-receipt");
  printButtons.forEach((button) => {
    button.addEventListener("click", function () {
      window.print();
    });
  });

  // Initialize real-time cart calculations if on cart page
  if (document.querySelector(".cart-item")) {
    initializeRealTimeCartCalculations();
  }
});

// Add to cart with quantity
function addToCart(productId) {
  const quantity = document.getElementById(`quantity-${productId}`)?.value || 1;

  const formData = new FormData();
  formData.append("product_id", productId);
  formData.append("quantity", quantity);

  fetch(`/add_to_cart/${productId}`, {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (response.ok) {
        // Show success message or update cart count
        location.reload();
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute("href")).scrollIntoView({
      behavior: "smooth",
    });
  });
});

// Cart quantity updates with real-time calculation
function initializeCartQuantityHandlers() {
  const quantityInputs = document.querySelectorAll(".quantity-input");
  quantityInputs.forEach((input) => {
    input.addEventListener("change", function () {
      const form = this.closest("form");
      if (form) {
        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn ? submitBtn.innerHTML : "";

        if (submitBtn) {
          submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
          submitBtn.disabled = true;
        }

        // Submit the form
        fetch(form.action, {
          method: "POST",
          body: new FormData(form),
        })
          .then((response) => {
            if (response.ok) {
              // If successful, the page will reload with updated cart
              window.location.reload();
            } else {
              throw new Error("Failed to update cart");
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            if (submitBtn) {
              submitBtn.innerHTML = originalText;
              submitBtn.disabled = false;
            }
            alert("Failed to update quantity. Please try again.");
          });
      }
    });
  });
}

// Real-time cart calculations for cart page
function initializeRealTimeCartCalculations() {
  // Function to format currency
  function formatCurrency(amount) {
    return (
      "₹" +
      amount.toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  }

  // Function to calculate and update totals
  function updateTotals() {
    let subtotal = 0;

    // Calculate subtotal from all items
    document.querySelectorAll(".cart-item").forEach((item) => {
      const quantityInput = item.querySelector(".quantity-input");
      const priceElement = item.querySelector(".item-price");
      const totalElement = item.querySelector(".item-total");

      if (quantityInput && priceElement && totalElement) {
        const quantity = parseInt(quantityInput.value) || 0;
        const price = parseFloat(priceElement.getAttribute("data-price")) || 0;
        const itemTotal = price * quantity;

        subtotal += itemTotal;

        // Update item total display
        totalElement.textContent = formatCurrency(itemTotal);
      }
    });

    // Calculate shipping (free above ₹999, else ₹50)
    const shipping = subtotal >= 999 ? 0 : 50;

    // Fixed tax amount as requested
    const tax = 300;

    // Calculate grand total
    const grandTotal = subtotal + shipping + tax;

    // Update summary display
    const subtotalElement = document.getElementById("subtotal");
    const shippingElement = document.getElementById("shipping");
    const taxElement = document.getElementById("tax");
    const grandTotalElement = document.getElementById("grand-total");

    if (subtotalElement) subtotalElement.textContent = formatCurrency(subtotal);
    if (shippingElement) shippingElement.textContent = formatCurrency(shipping);
    if (taxElement) taxElement.textContent = formatCurrency(tax);
    if (grandTotalElement)
      grandTotalElement.textContent = formatCurrency(grandTotal);

    // Update shipping message
    const shippingAlert = document.querySelector(".alert");
    if (shippingAlert) {
      if (subtotal >= 999) {
        shippingAlert.className = "alert alert-success";
        shippingAlert.innerHTML =
          '<i class="fas fa-shipping-fast me-2"></i>You qualify for free shipping!';
      } else {
        shippingAlert.className = "alert alert-info";
        const amountNeeded = 999 - subtotal;
        shippingAlert.innerHTML = `<small>Add ${formatCurrency(
          amountNeeded
        )} more for free shipping!</small>`;
      }
    }
  }

  // Auto-update totals when quantity changes
  document.querySelectorAll(".quantity-input").forEach((input) => {
    input.addEventListener("change", function () {
      // Update the display immediately
      updateTotals();

      // Submit the form to update the database
      const form = this.closest(".quantity-form");
      if (form) {
        // Use fetch to submit the form without page reload
        const formData = new FormData(form);

        fetch(form.action, {
          method: "POST",
          body: formData,
        })
          .then((response) => {
            if (response.ok) {
              console.log("Cart updated successfully");
            } else {
              console.error("Failed to update cart");
              // Revert the display if update failed
              updateTotals();
            }
          })
          .catch((error) => {
            console.error("Error updating cart:", error);
            // Revert the display if update failed
            updateTotals();
          });
      }
    });

    // Also update on input for real-time feedback
    input.addEventListener("input", function () {
      updateTotals();
    });
  });

  // Initialize totals on page load
  updateTotals();
}

// Utility function for cart operations
function updateCartQuantity(cartId, quantity) {
  const formData = new FormData();
  formData.append("action", "update");
  formData.append("quantity", quantity);

  return fetch(`/update_cart/${cartId}`, {
    method: "POST",
    body: formData,
  });
}

// Remove item from cart
function removeCartItem(cartId) {
  if (confirm("Are you sure you want to remove this item from your cart?")) {
    const formData = new FormData();
    formData.append("action", "remove");

    fetch(`/update_cart/${cartId}`, {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (response.ok) {
          window.location.reload();
        } else {
          alert("Failed to remove item. Please try again.");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Failed to remove item. Please try again.");
      });
  }
}

// Update cart item count in navbar
function updateCartCount(count) {
  const cartCountElement = document.querySelector(".navbar .badge");
  if (cartCountElement) {
    if (count > 0) {
      cartCountElement.textContent = count;
      cartCountElement.style.display = "inline";
    } else {
      cartCountElement.style.display = "none";
    }
  }
}

// Show loading spinner
function showLoading(element) {
  const originalHTML = element.innerHTML;
  element.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  element.disabled = true;
  return originalHTML;
}

// Hide loading spinner
function hideLoading(element, originalHTML) {
  element.innerHTML = originalHTML;
  element.disabled = false;
}

// Format phone number for display
function formatPhoneNumber(phone) {
  if (!phone) return "";
  // Remove any existing formatting
  const cleaned = phone.replace(/\D/g, "");
  // Format as +91 XXXXX XXXXX
  if (cleaned.length === 12 && cleaned.startsWith("91")) {
    return `+${cleaned.substring(0, 2)} ${cleaned.substring(
      2,
      7
    )} ${cleaned.substring(7)}`;
  }
  return phone;
}

// Validate email format
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Validate phone number format
function isValidPhone(phone) {
  const phoneRegex = /^\+91\s?\d{10}$/;
  return phoneRegex.test(phone.replace(/\s/g, ""));
}

// Show notification
function showNotification(message, type = "success") {
  // Create notification element
  const notification = document.createElement("div");
  notification.className = `alert alert-${type} alert-dismissible fade show`;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1060;
    min-width: 300px;
  `;
  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  // Add to page
  document.body.appendChild(notification);

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.remove();
    }
  }, 5000);
}

// Debounce function for performance
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Initialize all cart functionality
function initializeAllCartHandlers() {
  initializeCartQuantityHandlers();
  if (document.querySelector(".cart-item")) {
    initializeRealTimeCartCalculations();
  }
}

// Re-initialize when navigating with Turbolinks-like systems
if (typeof Turbo !== "undefined") {
  document.addEventListener("turbo:load", function () {
    initializeAllCartHandlers();
  });
}

// Export functions for use in other modules (if needed)
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    initializeCartQuantityHandlers,
    initializeRealTimeCartCalculations,
    updateCartQuantity,
    removeCartItem,
    updateCartCount,
    formatCurrency: function (amount) {
      return (
        "₹" +
        amount.toLocaleString("en-IN", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      );
    },
    showNotification,
    debounce,
  };
}
