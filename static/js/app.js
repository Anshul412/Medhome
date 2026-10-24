"use strict";

(() => {
  const dialog = document.getElementById("vitals-modal");
  const openButton = document.getElementById("open-vitals-modal");
  const closeButton = document.getElementById("close-vitals-modal");
  const cancelButton = document.getElementById("cancel-vitals-modal");

  if (!dialog || !openButton || !closeButton || !cancelButton) {
    return;
  }

  openButton.addEventListener("click", () => dialog.showModal());
  closeButton.addEventListener("click", () => dialog.close());
  cancelButton.addEventListener("click", () => dialog.close());

  if (dialog.querySelector("[role='alert']")) {
    dialog.showModal();
  }
})();
