import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getAnalytics, isSupported } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-analytics.js";

const firebaseConfig = {
  apiKey: "AIzaSyBa6kXfvPAPV5NTMnxRh_2o5xCA5bW-HsY",
  authDomain: "unitools-8d9c8.firebaseapp.com",
  projectId: "unitools-8d9c8",
  storageBucket: "unitools-8d9c8.firebasestorage.app",
  messagingSenderId: "555945920101",
  appId: "1:555945920101:web:e4ac91f31103a2dd00688c",
  measurementId: "G-Y2Q1SHGQ6B",
};

const app = initializeApp(firebaseConfig);
window.firebaseApp = app;

isSupported()
  .then((supported) => {
    if (!supported) {
      return;
    }
    const analytics = getAnalytics(app);
    window.firebaseAnalytics = analytics;
  })
  .catch(() => {
    // Ignore analytics setup failures on unsupported environments.
  });
