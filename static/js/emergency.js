"use strict";

(() => {
  const button = document.getElementById("share-location-whatsapp");
  const status = document.getElementById("location-status");
  const mapsLink = document.getElementById("location-map-link");
  const fallbackLink = document.getElementById("whatsapp-fallback");

  if (!button || !status) {
    return;
  }

  button.addEventListener("click", () => {
    if (!navigator.geolocation) {
      status.textContent =
        "Location sharing is not supported by this browser. Call your emergency contact directly.";
      return;
    }

    const phone = button.dataset.phone || "";
    const whatsappNumber = phone.replace(/\D/g, "");
    if (!whatsappNumber) {
      status.textContent =
        "A valid phone number is needed to prepare a WhatsApp message. Call emergency services if urgent.";
      return;
    }

    status.textContent = "Requesting permission to access your location…";
    button.disabled = true;
    const whatsappWindow = window.open("about:blank", "_blank");
    if (whatsappWindow) {
      whatsappWindow.opener = null;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        const mapUrl = `https://maps.google.com/?q=${latitude},${longitude}`;
        const message = `I may need help. My current location is: ${mapUrl}`;
        const whatsappUrl = new URL(`https://wa.me/${whatsappNumber}`);
        whatsappUrl.searchParams.set("text", message);

        if (mapsLink) {
          mapsLink.href = mapUrl;
          mapsLink.classList.remove("hidden");
        }

        if (fallbackLink) {
          fallbackLink.href = whatsappUrl.toString();
          fallbackLink.classList.remove("hidden");
        }
        status.textContent =
          "Location ready. WhatsApp will open so you can review and send it to your primary contact.";
        button.disabled = false;
        if (whatsappWindow) {
          whatsappWindow.location.replace(whatsappUrl.toString());
        } else {
          status.textContent += " If it did not open, use the WhatsApp link below.";
        }
      },
      (error) => {
        const messages = {
          1: "Location permission was denied. You can enable it in browser settings or call your contact directly.",
          2: "Your device could not determine a location. Try again or call your contact directly.",
          3: "The location request timed out. Try again or call your contact directly.",
        };
        status.textContent =
          messages[error.code] ||
          "Location could not be obtained. Call emergency services if urgent.";
        button.disabled = false;
        if (whatsappWindow) {
          whatsappWindow.close();
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 0,
      },
    );
  });
})();
