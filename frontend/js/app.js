const API_BASE_URL = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1") || window.location.origin.includes(":5000")
  ? window.location.origin
  : "https://custom-wear.onrender.com";

// Initialize system states
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  updateCartBadge();
  hidePageLoader();
  
  // Setup global event listeners
  const logoutBtn = document.getElementById("nav-logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", handleLogout);
  }
  
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", toggleTheme);
  }
  
  // Render login state in navbar
  syncNavbarAuth();
});

// Theme Management
function initTheme() {
  const savedTheme = localStorage.getItem("theme") || "dark";
  if (savedTheme === "light") {
    document.documentElement.classList.add("light");
    document.documentElement.classList.remove("dark");
  } else {
    document.documentElement.classList.add("dark");
    document.documentElement.classList.remove("light");
  }
}

function toggleTheme() {
  if (document.documentElement.classList.contains("light")) {
    document.documentElement.classList.remove("light");
    document.documentElement.classList.add("dark");
    localStorage.setItem("theme", "dark");
  } else {
    document.documentElement.classList.remove("dark");
    document.documentElement.classList.add("light");
    localStorage.setItem("theme", "light");
  }
}

// Page Loader Helpers
function showPageLoader() {
  const loader = document.getElementById("page-loader");
  if (loader) {
    loader.style.opacity = "1";
    loader.style.pointerEvents = "all";
    loader.style.display = "flex";
  }
}

function hidePageLoader() {
  const loader = document.getElementById("page-loader");
  if (loader) {
    loader.style.opacity = "0";
    loader.style.pointerEvents = "none";
    setTimeout(() => {
      loader.style.display = "none";
    }, 500);
  }
}

// Authentication Helpers
function getAuthToken() {
  return localStorage.getItem("auth_token");
}

function getCurrentUser() {
  const userStr = localStorage.getItem("user");
  return userStr ? JSON.parse(userStr) : null;
}

function saveSession(token, user) {
  localStorage.setItem("auth_token", token);
  localStorage.setItem("user", JSON.stringify(user));
  syncNavbarAuth();
}

function handleLogout(e) {
  if (e) e.preventDefault();
  localStorage.removeItem("auth_token");
  localStorage.removeItem("user");
  window.location.href = "index.html";
}

function syncNavbarAuth() {
  const token = getAuthToken();
  const user = getCurrentUser();
  
  const guestLinks = document.querySelectorAll(".auth-guest");
  const userLinks = document.querySelectorAll(".auth-user");
  const adminLinks = document.querySelectorAll(".auth-admin");
  const usernameText = document.getElementById("nav-username");
  
  if (token && user) {
    guestLinks.forEach(l => l.classList.add("hidden"));
    userLinks.forEach(l => l.classList.remove("hidden"));
    
    if (user.role === "admin") {
      adminLinks.forEach(l => l.classList.remove("hidden"));
    } else {
      adminLinks.forEach(l => l.classList.add("hidden"));
    }
    
    if (usernameText) {
      usernameText.textContent = user.name;
    }
  } else {
    guestLinks.forEach(l => l.classList.remove("hidden"));
    userLinks.forEach(l => l.classList.add("hidden"));
    adminLinks.forEach(l => l.classList.add("hidden"));
  }
}

// Fetch API Wrapper
async function apiRequest(endpoint, method = "GET", body = null) {
  const token = getAuthToken();
  const headers = {
    "Content-Type": "application/json"
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  const config = {
    method,
    headers
  };
  
  if (body) {
    config.body = JSON.stringify(body);
  }
  
  // Auto-prefix with /api if not present
  let urlPath = endpoint;
  if (!urlPath.startsWith("/api")) {
    urlPath = "/api" + (urlPath.startsWith("/") ? "" : "/") + urlPath;
  }
  
  try {
    const res = await fetch(`${API_BASE_URL}${urlPath}`, config);
    const data = await res.json();
    if (!res.ok) {
      // 401 = expired / invalid token — silently clear stale session
      if (res.status === 401) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user");
        if (typeof syncNavbarAuth === "function") syncNavbarAuth();
        // Throw a silent error (no toast — callers that need auth will redirect)
        const err = new Error(data.message || "Session expired.");
        err.isAuthError = true;
        throw err;
      }
      throw new Error(data.message || "Something went wrong!");
    }
    return data;
  } catch (err) {
    console.error("API Error: ", err);
    throw err;
  }
}

// Cart Management
function getLocalCart() {
  return JSON.parse(localStorage.getItem("cart") || "[]");
}

function saveLocalCart(items) {
  localStorage.setItem("cart", JSON.stringify(items));
  updateCartBadge();
}

function updateCartBadge() {
  const cart = getLocalCart();
  const badges = document.querySelectorAll(".cart-count-badge");
  const totalItems = cart.reduce((sum, item) => sum + parseInt(item.quantity || 1), 0);
  
  badges.forEach(badge => {
    badge.textContent = totalItems;
    if (totalItems > 0) {
      badge.classList.remove("hidden");
    } else {
      badge.classList.add("hidden");
    }
  });
}

function addToCart(item) {
  // item: { product_id, name, price, quantity, size, color, print_style, image, gsm }
  let cart = getLocalCart();
  const existingIdx = cart.findIndex(i => 
    i.product_id === item.product_id && 
    i.size === item.size && 
    i.color === item.color &&
    i.print_style === item.print_style &&
    (item.gsm ? i.gsm === item.gsm : true)
  );
  
  if (existingIdx > -1) {
    cart[existingIdx].quantity += parseInt(item.quantity || 1);
  } else {
    cart.push(item);
  }
  
  saveLocalCart(cart);
  
  // Sync with user account if logged in
  if (getAuthToken()) {
    apiRequest("/api/cart", "POST", { items: cart }).catch(err => console.error("Sync cart error", err));
  }
}

// Wishlist Management
function getLocalWishlist() {
  return JSON.parse(localStorage.getItem("wishlist") || "[]");
}

function saveLocalWishlist(list) {
  localStorage.setItem("wishlist", JSON.stringify(list));
}

function toggleWishlist(productId) {
  let list = getLocalWishlist();
  const idx = list.indexOf(productId);
  let added = false;
  
  if (idx > -1) {
    list.splice(idx, 1);
  } else {
    list.push(productId);
    added = true;
  }
  
  saveLocalWishlist(list);
  
  if (getAuthToken()) {
    apiRequest("/api/wishlist", "POST", { product_ids: list }).catch(err => console.error("Sync wishlist error", err));
  }
  return added;
}

// Message Banner helper
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container") || createToastContainer();
  const toast = document.createElement("div");
  toast.className = `px-5 py-3 rounded-lg shadow-lg border backdrop-blur-md transition duration-300 transform translate-y-2 opacity-0 text-sm font-medium ${
    type === "success" 
      ? "bg-green-500/20 border-green-500/30 text-green-300" 
      : "bg-red-500/20 border-red-500/30 text-red-300"
  }`;
  toast.textContent = message;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.remove("translate-y-2", "opacity-0");
  }, 10);
  
  setTimeout(() => {
    toast.classList.add("translate-y-2", "opacity-0");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toast-container";
  container.className = "fixed bottom-5 right-5 z-[99999] flex flex-col gap-2";
  document.body.appendChild(container);
  return container;
}

// ─── Saved Addresses ───────────────────────────────────────────────────────
// Saves a shipping address to localStorage (max 3, newest first, no duplicates)
function saveShippingAddress(addr) {
  if (!addr || !addr.name || !addr.address) return;
  let saved = getSavedAddresses();
  // Remove duplicate by matching name + pin + address
  saved = saved.filter(a =>
    !(a.name === addr.name && a.pin === addr.pin && a.address === addr.address)
  );
  saved.unshift(addr);          // newest first
  saved = saved.slice(0, 3);    // keep max 3
  localStorage.setItem("saved_addresses", JSON.stringify(saved));
}

function getSavedAddresses() {
  return JSON.parse(localStorage.getItem("saved_addresses") || "[]");
}

// ─── Mobile Navigation Menu ─────────────────────────────────────────────
function toggleMobileMenu() {
  const menu = document.getElementById("mobile-menu");
  const icon = document.getElementById("mobile-menu-icon");
  if (!menu) return;
  const isHidden = menu.classList.toggle("hidden");
  if (icon) {
    icon.setAttribute("data-lucide", isHidden ? "menu" : "x");
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
  }
}

// Close mobile menu on resize above lg (1024px)
window.addEventListener("resize", () => {
  if (window.innerWidth >= 1024) {
    const menu = document.getElementById("mobile-menu");
    const icon = document.getElementById("mobile-menu-icon");
    if (menu && !menu.classList.contains("hidden")) {
      menu.classList.add("hidden");
      if (icon) {
        icon.setAttribute("data-lucide", "menu");
        if (window.lucide && typeof window.lucide.createIcons === "function") {
          window.lucide.createIcons();
        }
      }
    }
  }
});

