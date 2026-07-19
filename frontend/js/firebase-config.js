// ============================================================
//  CUSTOM WEAR & CRADANCE — Firebase Web Client Configuration
//  Project: project-00cb5ede-0325-438b-947
// ============================================================
const firebaseConfig = {
  apiKey: "AIzaSyA-hnXP-w2EP6IOspMGv5V3eWCJjr6Owag",
  authDomain: "project-00cb5ede-0325-438b-947.firebaseapp.com",
  projectId: "project-00cb5ede-0325-438b-947",
  storageBucket: "project-00cb5ede-0325-438b-947.firebasestorage.app",
  messagingSenderId: "445453811210",
  appId: "1:445453811210:web:bb7b6733dcb0fef956e9f3"
};

// ============================================================
//  Firebase Initialization (safe — prevents double-init errors)
// ============================================================
let firebaseInitialized = false;
let firebaseApp = null;

if (typeof firebase !== 'undefined') {
  try {
    // Use existing app if already initialized (e.g., script loaded twice)
    if (!firebase.apps.length) {
      firebaseApp = firebase.initializeApp(firebaseConfig);
    } else {
      firebaseApp = firebase.app();
    }
    firebaseInitialized = true;
    console.log("[Firebase] ✅ Frontend SDK Initialized — Project:", firebaseConfig.projectId);

    // ── Persist auth state across page loads ──
    firebase.auth().onAuthStateChanged(function(user) {
      if (user) {
        // Firebase session is active: refresh backend JWT silently
        user.getIdToken().then(function(idToken) {
          // Only refresh if we don't already have a local JWT
          const existing = localStorage.getItem("auth_token");
          if (!existing) {
            apiRequest("/api/auth/google-login", "POST", {
              email: user.email,
              name: user.displayName || user.email.split("@")[0]
            }).then(data => {
              if (data && data.token) {
                localStorage.setItem("auth_token", data.token);
                localStorage.setItem("user", JSON.stringify(data.user));
                console.log("[Firebase] ↺ Session restored for:", user.email);
                // Trigger navbar re-render if available
                if (typeof syncNavbarAuth === "function") syncNavbarAuth();
              }
            }).catch(() => {});
          }
        });
      }
    });

  } catch (e) {
    console.warn("[Firebase] ⚠ SDK failed to initialize. Falling back to local API mode:", e.message);
  }
} else {
  console.warn("[Firebase] SDK not loaded. Firebase scripts may be missing from this page.");
}

// ============================================================
//  Auth Helper Functions (Firebase + Local Flask fallback)
// ============================================================

/**
 * Login with email & password.
 * Tries Firebase Auth first, falls back to Flask JWT if Firebase fails.
 */
async function performLogin(email, password) {
  if (firebaseInitialized) {
    try {
      const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
      const data = await apiRequest("/api/auth/google-login", "POST", {
        email: userCredential.user.email,
        name: userCredential.user.displayName || email.split("@")[0]
      });
      return data;
    } catch (e) {
      // If Firebase throws auth/wrong-password or similar, propagate it
      if (e.code && e.code.startsWith("auth/")) throw e;
      console.warn("[Firebase Auth] Non-auth error, falling back to local login:", e.message);
    }
  }
  // Local Flask JWT login
  return await apiRequest("/api/auth/login", "POST", { email, password });
}

/**
 * Register a new account.
 * Creates Firebase Auth user first, then registers in Flask backend.
 */
async function performRegister(name, email, password) {
  if (firebaseInitialized) {
    try {
      const userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
      await userCredential.user.updateProfile({ displayName: name });
      const data = await apiRequest("/api/auth/google-login", "POST", { email, name });
      return data;
    } catch (e) {
      if (e.code && e.code.startsWith("auth/")) throw e;
      console.warn("[Firebase Register] Non-auth error, falling back to local register:", e.message);
    }
  }
  // Local Flask register
  return await apiRequest("/api/auth/register", "POST", { name, email, password });
}

/**
 * Google One-Tap / Popup login.
 * Falls back to a demo simulation if Firebase is not ready.
 */
async function performGoogleLogin() {
  if (firebaseInitialized) {
    try {
      const provider = new firebase.auth.GoogleAuthProvider();
      provider.addScope("profile");
      provider.addScope("email");
      const result = await firebase.auth().signInWithPopup(provider);
      const data = await apiRequest("/api/auth/google-login", "POST", {
        email: result.user.email,
        name: result.user.displayName || result.user.email.split("@")[0]
      });
      return data;
    } catch (e) {
      if (e.code === "auth/popup-closed-by-user") {
        throw new Error("Google sign-in cancelled.");
      }
      console.error("[Firebase Google Login] error:", e);
      throw e;
    }
  }

  // Simulation fallback (only in dev/demo mode)
  console.warn("[Firebase] Not initialized — simulating Google Login for demo.");
  if (typeof showToast === "function") showToast("Firebase not set up. Running in demo mode.", "warning");
  return await apiRequest("/api/auth/google-login", "POST", {
    email: "demo.user@gmail.com",
    name: "Demo User"
  });
}

/**
 * Sign out from Firebase and clear local session.
 */
async function performLogout() {
  if (firebaseInitialized) {
    try {
      await firebase.auth().signOut();
    } catch (e) {
      console.warn("[Firebase] Signout error:", e.message);
    }
  }
  localStorage.removeItem("auth_token");
  localStorage.removeItem("user");
  window.location.href = "index.html";
}