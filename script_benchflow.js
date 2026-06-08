// ==========================================
// LOCAL STORAGE MANAGER
// ==========================================
class LocalStorageManager {
  constructor(storageKey = "benchflow_auftraege") {
    this.storageKey = storageKey;
    this.storageVersion = "0.1";
  }

  save(data) {
    try {
      const payload = {
        version: this.storageVersion,
        timestamp: new Date().toISOString(),
        count: data.length,
        data: data,
      };

      localStorage.setItem(this.storageKey, JSON.stringify(payload));
      console.log(`✅ ${data.length} Aufträge gespeichert`);
      return true;
    } catch (error) {
      console.error("❌ Fehler beim Speichern:", error);
      Toast.error("Fehler beim Speichern der Daten");
      return false;
    }
  }

  load() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (!stored) {
        console.log("ℹ️ Keine gespeicherten Aufträge gefunden");
        return null;
      }

      const payload = JSON.parse(stored);

      if (!payload.data || !Array.isArray(payload.data)) {
        console.warn("⚠️ Ungültige Datenstruktur");
        return null;
      }

      console.log(`✅ ${payload.count} Aufträge geladen`);
      return payload.data;
    } catch (error) {
      console.error("❌ Fehler beim Laden:", error);
      Toast.error("Fehler beim Laden der Daten");
      return null;
    }
  }

  clear() {
    try {
      localStorage.removeItem(this.storageKey);
      console.log("✅ Daten gelöscht");
      return true;
    } catch (error) {
      console.error("❌ Fehler beim Löschen:", error);
      return false;
    }
  }

  exportToJSON(data) {
    try {
      const exportData = {
        exported: new Date().toISOString(),
        version: this.storageVersion,
        count: data.length,
        orders: data,
      };

      const jsonString = JSON.stringify(exportData, null, 2);
      const blob = new Blob([jsonString], { type: "application/json" });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = `benchflow_export_${new Date().toISOString().slice(0, 10)}.json`;
      link.click();

      URL.revokeObjectURL(url);
      Toast.success("Daten erfolgreich exportiert");
    } catch (error) {
      console.error("❌ Export-Fehler:", error);
      Toast.error("Fehler beim Exportieren");
    }
  }

  importFromJSON(file) {
    return new Promise((resolve, reject) => {
      if (!file || file.type !== "application/json") {
        Toast.error("Bitte eine gültige JSON-Datei auswählen");
        reject(new Error("Ungültiger Dateityp"));
        return;
      }

      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          const data = imported.orders || imported.data || imported;

          if (!Array.isArray(data)) {
            throw new Error("Keine gültige Auftragsliste gefunden");
          }

          resolve(data);
        } catch (error) {
          console.error("❌ Import-Fehler:", error);
          Toast.error("Fehler beim Importieren");
          reject(error);
        }
      };

      reader.onerror = () => {
        Toast.error("Fehler beim Lesen der Datei");
        reject(new Error("FileReader Error"));
      };

      reader.readAsText(file);
    });
  }
}

const storageManager = new LocalStorageManager();

// ==========================================
// TOAST SYSTEM
// ==========================================
const Toast = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.className = "toast-container";
      document.body.appendChild(this.container);
    }
  },

  show(message, type = "info", duration = 3000) {
    this.init();

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;

    this.container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, duration);
  },

  success(message) {
    this.show(message, "success");
  },

  error(message) {
    this.show(message, "error");
  },

  info(message) {
    this.show(message, "info");
  },
};

// ==========================================
// FORM VALIDATOR
// ==========================================
const FormValidator = {
  validateField(field) {
    if (field.disabled) return true;

    if (field.tagName === "SELECT" && field.required && field.value === "") {
      this.showFieldError(
        field,
        field.dataset.errorRequired || "Bitte eine Option wählen",
      );
      return false;
    }

    if (!field.checkValidity()) {
      let errorMessage = "Ungültige Eingabe";

      if (field.validity.valueMissing) {
        errorMessage = field.dataset.errorRequired || "Pflichtfeld";
      } else if (field.validity.typeMismatch) {
        errorMessage = field.dataset.errorTypemismatch || "Ungültiges Format";
      } else if (field.validity.tooShort) {
        errorMessage = `Mindestens ${field.minLength} Zeichen`;
      }

      this.showFieldError(field, errorMessage);
      return false;
    }

    this.clearFieldError(field);
    return true;
  },

  showFieldError(field, message) {
    const errorSpan = document.getElementById(`${field.id}-error`);
    if (errorSpan) {
      errorSpan.textContent = message;
    }
    field.setAttribute("aria-invalid", "true");
  },

  clearFieldError(field) {
    const errorSpan = document.getElementById(`${field.id}-error`);
    if (errorSpan) {
      errorSpan.textContent = "";
    }
    field.setAttribute("aria-invalid", "false");
  },

  validateForm(form) {
    let isValid = true;
    let firstInvalidField = null;

    form.querySelectorAll("[required]").forEach((field) => {
      if (!this.validateField(field)) {
        isValid = false;
        if (!firstInvalidField) {
          firstInvalidField = field;
        }
      }
    });

    if (!isValid && firstInvalidField) {
      firstInvalidField.focus();
      Toast.error("Bitte alle Pflichtfelder korrekt ausfüllen");
    }

    return isValid;
  },
};

// ==========================================
// EMPTY STATE MANAGER
// ==========================================
const EmptyStateManager = {
  states: {
    empty: "emptyState",
    welcome: "welcomeState",
    noResults: "noSearchResults",
  },

  show(stateType, data = {}) {
    const table = document.querySelector(".mitarbeiter-table");
    if (table) table.style.display = "none";

    Object.values(this.states).forEach((stateId) => {
      const state = document.getElementById(stateId);
      if (state) state.style.display = "none";
    });

    const currentState = document.getElementById(this.states[stateType]);
    if (currentState) {
      currentState.style.display = "block";

      if (stateType === "noResults" && data.searchTerm) {
        const termSpan = currentState.querySelector("#searchTerm");
        if (termSpan) termSpan.textContent = data.searchTerm;
      }
    }
  },

  hide() {
    Object.values(this.states).forEach((stateId) => {
      const state = document.getElementById(stateId);
      if (state) state.style.display = "none";
    });

    const table = document.querySelector(".mitarbeiter-table");
    if (table) table.style.display = "table";
  },
};

// ==========================================
// MAIN
// ==========================================
document.addEventListener("DOMContentLoaded", function () {
  let auftraege = [];
  let aktuelleDaten = [];
  let aktuelleSeite = 1;
  const eintraegeProSeite = 10;
  let editModus = false;
  let editId = null;
  let aktuellerSort = null;
  let sortRichtung = "asc";

  const demoAuftraege = [
    {
      id: crypto.randomUUID(),
      auftragsnummer: "BF-2026-0001",
      kundeName: "Max Mustermann",
      kundeEmail: "max@example.de",
      kundeTelefon: "+49 170 1111111",
      kategorie: "gitarre",
      hersteller: "Fender",
      modell: "Stratocaster",
      seriennummer: "SN-FEN-1001",
      zubehoer: "Case, Gurt",
      zustand: "Leichte Kratzer",
      fehlerbeschreibung: "Kein Signal am Output, Wackelkontakt",
      status: "in_pruefung",
      techniker: "M. Osypka",
      garantie: "nein",
      kvErforderlich: "ja",
      geraetBild: "",
      erstelltAm: new Date().toISOString(),
    },
    {
      id: crypto.randomUUID(),
      auftragsnummer: "BF-2026-0002",
      kundeName: "Julia Becker",
      kundeEmail: "julia@example.de",
      kundeTelefon: "+49 170 2222222",
      kategorie: "keyboard",
      hersteller: "Yamaha",
      modell: "P-125",
      seriennummer: "SN-YAM-2002",
      zubehoer: "Netzteil",
      zustand: "Guter Zustand",
      fehlerbeschreibung: "Taste klemmt im mittleren Bereich",
      status: "wartet_freigabe",
      techniker: "A. Test",
      garantie: "unbekannt",
      kvErforderlich: "ja",
      geraetBild: "",
      erstelltAm: new Date().toISOString(),
    },
  ];

  const tabelleBody = document.getElementById("tabelleBody");
  const sucheInput = document.getElementById("suche");
  const filterStatus = document.getElementById("filterStatus");
  const filterKategorie = document.getElementById("filterKategorie");
  const form = document.getElementById("auftragForm");
  const neuBtn = document.getElementById("neuAuftrag");
  const abbrechenBtn = document.getElementById("abbrechen");
  const prevPageBtn = document.getElementById("prevPage");
  const nextPageBtn = document.getElementById("nextPage");
  const pageInfo = document.getElementById("pageInfo");
  const modal = document.getElementById("detailModal");
  const detailContent = document.getElementById("detailContent");
  const exportBtn = document.getElementById("exportBtn");
  const importBtn = document.getElementById("importBtn");
  const resetBtn = document.getElementById("resetBtn");
  const importFileInput = document.getElementById("importFileInput");
  const geraetBildInput = document.getElementById("geraetBild");

  function loadAuftraege() {
    const localData = storageManager.load();

    if (localData && localData.length > 0) {
      auftraege = localData;
      Toast.info(`${auftraege.length} Aufträge geladen`);
      return;
    }

    auftraege = demoAuftraege;
    storageManager.save(auftraege);
  }

  function checkActiveFilters() {
    return (
      sucheInput.value.trim() !== "" ||
      filterStatus.value !== "" ||
      filterKategorie.value !== ""
    );
  }

  function renderTabelle(daten) {
    if (!daten || daten.length === 0) {
      const searchTerm = sucheInput.value.trim();

      if (searchTerm) {
        EmptyStateManager.show("noResults", { searchTerm });
      } else if (checkActiveFilters()) {
        EmptyStateManager.show("empty");
      } else {
        EmptyStateManager.show("welcome");
      }

      tabelleBody.innerHTML = "";
      return;
    }

    EmptyStateManager.hide();
    tabelleBody.innerHTML = "";

    daten.forEach((auftrag) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${auftrag.auftragsnummer}</td>
        <td>${auftrag.kundeName}</td>
        <td>${auftrag.kategorie}</td>
        <td>${auftrag.hersteller}</td>
        <td>${auftrag.modell}</td>
        <td>${auftrag.seriennummer || "-"}</td>
        <td>${auftrag.status}</td>
        <td>${auftrag.techniker || "-"}</td>
        <td class="action-buttons">
          <button class="detailBtn" data-id="${auftrag.id}">Detail</button>
          <button class="editBtn" data-id="${auftrag.id}">Edit</button>
          <button class="deleteBtn" data-id="${auftrag.id}">Delete</button>
        </td>
      `;
      tabelleBody.appendChild(row);
    });
  }

  function renderPaginierung(gesamtSeiten, gesamtEintraege) {
    pageInfo.textContent = `Seite ${aktuelleSeite} von ${gesamtSeiten} (${gesamtEintraege} Einträge)`;
    prevPageBtn.disabled = aktuelleSeite === 1;
    nextPageBtn.disabled = aktuelleSeite >= gesamtSeiten;
  }

  function zeigeDetails(auftrag) {
    detailContent.innerHTML = `
      <p><strong>Auftragsnummer:</strong> ${auftrag.auftragsnummer}</p>
      <p><strong>Kunde:</strong> ${auftrag.kundeName}</p>
      <p><strong>E-Mail:</strong> ${auftrag.kundeEmail || "-"}</p>
      <p><strong>Telefon:</strong> ${auftrag.kundeTelefon}</p>
      <p><strong>Kategorie:</strong> ${auftrag.kategorie}</p>
      <p><strong>Hersteller:</strong> ${auftrag.hersteller}</p>
      <p><strong>Modell:</strong> ${auftrag.modell}</p>
      <p><strong>Seriennummer:</strong> ${auftrag.seriennummer || "-"}</p>
      <p><strong>Zubehör:</strong> ${auftrag.zubehoer || "-"}</p>
      <p><strong>Zustand:</strong> ${auftrag.zustand || "-"}</p>
      <p><strong>Fehlerbeschreibung:</strong> ${auftrag.fehlerbeschreibung}</p>
      <p><strong>Status:</strong> ${auftrag.status}</p>
      <p><strong>Techniker:</strong> ${auftrag.techniker || "-"}</p>
      <p><strong>Garantie:</strong> ${auftrag.garantie || "-"}</p>
      <p><strong>KV erforderlich:</strong> ${auftrag.kvErforderlich || "-"}</p>
    `;

    modal.classList.remove("hidden");
  }

  function erstelleAuftrag(neuerAuftrag) {
    auftraege.push(neuerAuftrag);

    if (storageManager.save(auftraege)) {
      aktuelleSeite = 1;
      aktualisiereListe();
      Toast.success("Auftrag angelegt");
    } else {
      auftraege.pop();
    }
  }

  function aktualisiereAuftrag(id, updateData) {
    const index = auftraege.findIndex((a) => a.id === id);
    if (index === -1) return;

    const backup = { ...auftraege[index] };
    auftraege[index] = { ...auftraege[index], ...updateData };

    if (storageManager.save(auftraege)) {
      aktualisiereListe();
      Toast.success("Auftrag aktualisiert");
    } else {
      auftraege[index] = backup;
    }
  }

  function loescheAuftrag(id) {
    const auftrag = auftraege.find((a) => a.id === id);
    if (!auftrag) return;

    const bestaetigung = confirm(
      `Auftrag wirklich löschen?\n\n${auftrag.auftragsnummer} | ${auftrag.kundeName} | ${auftrag.hersteller} ${auftrag.modell}`,
    );

    if (!bestaetigung) return;

    const index = auftraege.findIndex((a) => a.id === id);
    const backup = auftraege[index];
    auftraege.splice(index, 1);

    if (storageManager.save(auftraege)) {
      aktualisiereListe();
      Toast.success("Auftrag gelöscht");
    } else {
      auftraege.splice(index, 0, backup);
    }
  }

  function oeffneBearbeitungsFormular(id) {
    const auftrag = auftraege.find((a) => a.id === id);
    if (!auftrag) return;

    editModus = true;
    editId = id;
    form.classList.remove("hidden");

    form.elements.kundeName.value = auftrag.kundeName || "";
    form.elements.kundeEmail.value = auftrag.kundeEmail || "";
    form.elements.kundeTelefon.value = auftrag.kundeTelefon || "";
    form.elements.kategorie.value = auftrag.kategorie || "";
    form.elements.hersteller.value = auftrag.hersteller || "";
    form.elements.modell.value = auftrag.modell || "";
    form.elements.seriennummer.value = auftrag.seriennummer || "";
    form.elements.zubehoer.value = auftrag.zubehoer || "";
    form.elements.zustand.value = auftrag.zustand || "";
    form.elements.fehlerbeschreibung.value = auftrag.fehlerbeschreibung || "";
    form.elements.status.value = auftrag.status || "";
    form.elements.techniker.value = auftrag.techniker || "";
    form.elements.garantie.value = auftrag.garantie || "";
    form.elements.kvErforderlich.value = auftrag.kvErforderlich || "nein";

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.textContent = "💾 Auftrag aktualisieren";

    form.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function sortiereTabelle(spalte) {
    if (aktuellerSort === spalte) {
      sortRichtung = sortRichtung === "asc" ? "desc" : "asc";
    } else {
      aktuellerSort = spalte;
      sortRichtung = "asc";
    }

    aktualisiereHeaderIcons(spalte);
    aktualisiereListe();
  }

  function aktualisiereHeaderIcons(aktiveSpalte) {
    document.querySelectorAll("th.sortable").forEach((th) => {
      th.classList.remove("sort-asc", "sort-desc");
    });

    const aktiverHeader = document.querySelector(
      `th[data-sort="${aktiveSpalte}"]`,
    );

    if (aktiverHeader) {
      aktiverHeader.classList.add(
        sortRichtung === "asc" ? "sort-asc" : "sort-desc",
      );
    }
  }

  function aktualisiereListe() {
    let gefiltert = [...auftraege];

    const suchbegriff = sucheInput.value.toLowerCase().trim();
    if (suchbegriff) {
      gefiltert = gefiltert.filter(
        (a) =>
          (a.auftragsnummer || "").toLowerCase().includes(suchbegriff) ||
          (a.kundeName || "").toLowerCase().includes(suchbegriff) ||
          (a.hersteller || "").toLowerCase().includes(suchbegriff) ||
          (a.modell || "").toLowerCase().includes(suchbegriff) ||
          (a.seriennummer || "").toLowerCase().includes(suchbegriff),
      );
    }

    if (filterStatus.value) {
      gefiltert = gefiltert.filter((a) => a.status === filterStatus.value);
    }

    if (filterKategorie.value) {
      gefiltert = gefiltert.filter((a) => a.kategorie === filterKategorie.value);
    }

    if (aktuellerSort) {
      gefiltert.sort((a, b) => {
        let valA = a[aktuellerSort] || "";
        let valB = b[aktuellerSort] || "";

        if (typeof valA === "string") valA = valA.toLowerCase();
        if (typeof valB === "string") valB = valB.toLowerCase();

        if (sortRichtung === "asc") {
          return valA > valB ? 1 : valA < valB ? -1 : 0;
        }
        return valA < valB ? 1 : valA > valB ? -1 : 0;
      });
    }

    aktuelleDaten = gefiltert;

    const gesamtEintraege = gefiltert.length;
    const gesamtSeiten = Math.ceil(gesamtEintraege / eintraegeProSeite) || 1;

    if (aktuelleSeite > gesamtSeiten) {
      aktuelleSeite = gesamtSeiten;
    }

    const start = (aktuelleSeite - 1) * eintraegeProSeite;
    const ende = start + eintraegeProSeite;
    const seiteDaten = gefiltert.slice(start, ende);

    renderTabelle(seiteDaten);
    renderPaginierung(gesamtSeiten, gesamtEintraege);
  }

  function leseBildAlsBase64(file) {
    return new Promise((resolve, reject) => {
      if (!file) {
        resolve("");
        return;
      }

      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () =>
        reject(new Error("Bild konnte nicht gelesen werden"));
      reader.readAsDataURL(file);
    });
  }

  // ==========================================
  // EVENTS
  // ==========================================
  neuBtn.addEventListener("click", () => {
    form.classList.remove("hidden");
  });

  abbrechenBtn.addEventListener("click", () => {
    form.classList.add("hidden");
    form.reset();
    editModus = false;
    editId = null;

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.textContent = "💾 Auftrag speichern";
  });

  form
    .querySelectorAll("input[required], select[required], textarea[required]")
    .forEach((field) => {
      field.addEventListener("blur", () => FormValidator.validateField(field));
      field.addEventListener("input", () => FormValidator.clearFieldError(field));
      field.addEventListener("change", () =>
        FormValidator.clearFieldError(field),
      );
    });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!FormValidator.validateForm(form)) return;

    let geraetBild = "";

    if (editModus) {
      const existing = auftraege.find((a) => a.id === editId);
      geraetBild = existing?.geraetBild || "";
    }

    if (geraetBildInput.files && geraetBildInput.files[0]) {
      try {
        geraetBild = await leseBildAlsBase64(geraetBildInput.files[0]);
      } catch (error) {
        Toast.error("Gerätebild konnte nicht verarbeitet werden");
        return;
      }
    }

    const payload = {
      kundeName: form.elements.kundeName.value,
      kundeEmail: form.elements.kundeEmail.value,
      kundeTelefon: form.elements.kundeTelefon.value,
      kategorie: form.elements.kategorie.value,
      hersteller: form.elements.hersteller.value,
      modell: form.elements.modell.value,
      seriennummer: form.elements.seriennummer.value,
      zubehoer: form.elements.zubehoer.value,
      zustand: form.elements.zustand.value,
      fehlerbeschreibung: form.elements.fehlerbeschreibung.value,
      status: form.elements.status.value,
      techniker: form.elements.techniker.value,
      garantie: form.elements.garantie.value,
      kvErforderlich: form.elements.kvErforderlich.value,
      geraetBild: geraetBild,
    };

    if (editModus) {
      aktualisiereAuftrag(editId, payload);
      editModus = false;
      editId = null;
      form.querySelector('button[type="submit"]').textContent =
        "💾 Auftrag speichern";
    } else {
      erstelleAuftrag({
        id: crypto.randomUUID(),
        auftragsnummer: `BF-${new Date().getFullYear()}-${String(auftraege.length + 1).padStart(4, "0")}`,
        erstelltAm: new Date().toISOString(),
        ...payload,
      });
    }

    form.reset();
    form.classList.add("hidden");
  });

  sucheInput.addEventListener("input", () => {
    aktuelleSeite = 1;
    aktualisiereListe();
  });

  filterStatus.addEventListener("change", () => {
    aktuelleSeite = 1;
    aktualisiereListe();
  });

  filterKategorie.addEventListener("change", () => {
    aktuelleSeite = 1;
    aktualisiereListe();
  });

  document.getElementById("filterReset").addEventListener("click", () => {
    sucheInput.value = "";
    filterStatus.value = "";
    filterKategorie.value = "";
    aktuelleSeite = 1;
    aktuellerSort = null;
    sortRichtung = "asc";

    document.querySelectorAll("th.sortable").forEach((th) => {
      th.classList.remove("sort-asc", "sort-desc");
    });

    aktualisiereListe();
    Toast.info("Filter zurückgesetzt");
  });

  document.addEventListener("click", (event) => {
    if (event.target.classList.contains("detailBtn")) {
      const id = event.target.dataset.id;
      const auftrag = auftraege.find((a) => a.id === id);
      if (auftrag) zeigeDetails(auftrag);
    }

    if (event.target.classList.contains("editBtn")) {
      oeffneBearbeitungsFormular(event.target.dataset.id);
    }

    if (event.target.classList.contains("deleteBtn")) {
      loescheAuftrag(event.target.dataset.id);
    }

    if (event.target.classList.contains("close") || event.target === modal) {
      modal.classList.add("hidden");
    }
  });

  prevPageBtn.addEventListener("click", () => {
    if (aktuelleSeite > 1) {
      aktuelleSeite--;
      aktualisiereListe();
    }
  });

  nextPageBtn.addEventListener("click", () => {
    const gesamtSeiten = Math.ceil(aktuelleDaten.length / eintraegeProSeite) || 1;

    if (aktuelleSeite < gesamtSeiten) {
      aktuelleSeite++;
      aktualisiereListe();
    }
  });

  document.querySelectorAll("th.sortable").forEach((th) => {
    th.addEventListener("click", () => {
      sortiereTabelle(th.dataset.sort);
    });
  });

  exportBtn.addEventListener("click", () => {
    if (auftraege.length === 0) {
      Toast.info("Keine Aufträge zum Exportieren");
      return;
    }

    storageManager.exportToJSON(auftraege);
  });

  importBtn.addEventListener("click", () => {
    importFileInput.click();
  });

  importFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const imported = await storageManager.importFromJSON(file);
      auftraege = imported;
      storageManager.save(auftraege);
      aktuelleSeite = 1;
      aktualisiereListe();
      Toast.success(`${auftraege.length} Aufträge importiert`);
    } catch (error) {
      console.error(error);
      Toast.error("Import fehlgeschlagen");
    }

    importFileInput.value = "";
  });

  resetBtn.addEventListener("click", () => {
    const bestaetigung = confirm(
      "Alle gespeicherten BenchFlow-Daten löschen und Demo-Daten wiederherstellen?",
    );

    if (!bestaetigung) return;

    storageManager.clear();
    auftraege = [...demoAuftraege];
    storageManager.save(auftraege);
    aktuelleSeite = 1;
    aktualisiereListe();
    Toast.success("Daten zurückgesetzt");
  });

  // ==========================================
  // INIT
  // ==========================================
  loadAuftraege();
  aktualisiereListe();

  console.log("BenchFlow v0.1 initialisiert");
});