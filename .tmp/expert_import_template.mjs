import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const output = "C:/Users/hamza/Desktop/mvp/static/downloads/modele_import_experts_orbit.xlsx";
await fs.mkdir("C:/Users/hamza/Desktop/mvp/static/downloads", { recursive: true });

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Experts");
sheet.showGridLines = false;
sheet.getRange("A1:P1").merge();
sheet.getRange("A1").values = [["ORBIT — Modèle d’import d’experts"]];
sheet.getRange("A2:P2").merge();
sheet.getRange("A2").values = [["Renseignez une ligne par expert. Les colonnes avec * sont obligatoires. Les listes utilisent une virgule comme séparateur."]];
sheet.getRange("A4:P4").values = [[
  "Matricule *", "Prénom *", "Nom *", "Fonction *", "Code filiale", "Domaines", "Compétences", "Certifications", "Verticales", "Langues (Nom:Niveau)", "TJM", "Devise", "Disponibilité", "Date disponibilité", "Présentation", "Statut validation"
]];
sheet.getRange("A5:P6").values = [[
  "EXP-2026-001", "Aïcha", "Diallo", "Architecte Cloud", "SN", "Cloud & infrastructure", "Azure, Kubernetes", "Azure Solutions Architect", "Télécoms", "Français:C1, Anglais:B2", 650, "EUR", "AVAILABLE", new Date("2026-10-01"), "Expertise cloud, architecture et accompagnement des équipes.", "APPROVED"
], [
  "EXP-2026-002", "Omar", "Kone", "Ingénieur Data", "SN", "Data & IA", "Python, SQL", "", "Télécoms, Finance", "Français:C1", 500, "EUR", "AVAILABLE", new Date("2026-10-15"), "", "DRAFT"
]];
sheet.getRange("A8:P8").merge();
sheet.getRange("A8").values = [["Valeurs autorisées : disponibilité = AVAILABLE, PRE_AGREEMENT, ON_MISSION, UNAVAILABLE. Statut validation = DRAFT, SUBMITTED, APPROVED, REJECTED. Niveaux de langue = A1 à C2."]];
sheet.getRange("A10:P10").merge();
sheet.getRange("A10").values = [["Règles d’import : un matricule ne peut exister qu’une fois. Un administrateur fournisseur ne peut importer que dans sa propre filiale. Les domaines, compétences, certifications, verticales et langues absents sont créés lors de l’import."]];
sheet.getRange("A1:P1").format = { fill: "#191D22", font: { name: "Arial", size: 16, bold: true, color: "#FFFFFF" }, verticalAlignment: "center" };
sheet.getRange("A2:P2").format = { font: { name: "Arial", size: 10, italic: true, color: "#657080" }, wrapText: true, verticalAlignment: "center" };
sheet.getRange("A4:P4").format = { fill: "#FF7900", font: { name: "Arial", size: 10, bold: true, color: "#1A1A1A" }, verticalAlignment: "center", horizontalAlignment: "center", wrapText: true, borders: { preset: "all", style: "thin", color: "#E86E00" } };
sheet.getRange("A5:P6").format = { font: { name: "Arial", size: 10, color: "#17202B" }, verticalAlignment: "center", borders: { preset: "inside", style: "thin", color: "#E5E7EB" } };
sheet.getRange("A8:P8").format = { fill: "#FFF3DD", font: { name: "Arial", size: 10, color: "#9B5A06" }, wrapText: true, verticalAlignment: "center" };
sheet.getRange("A10:P10").format = { fill: "#F4F5F7", font: { name: "Arial", size: 10, color: "#657080" }, wrapText: true, verticalAlignment: "center" };
sheet.getRange("A1:P10").format.font = { name: "Arial" };
sheet.getRange("A1:P1").format.rowHeight = 28;
sheet.getRange("A2:P2").format.rowHeight = 28;
sheet.getRange("A4:P4").format.rowHeight = 34;
sheet.getRange("A8:P8").format.rowHeight = 32;
sheet.getRange("A10:P10").format.rowHeight = 38;
for (const [column,width] of [["A",18],["B",14],["C",16],["D",24],["E",14],["F",25],["G",28],["H",28],["I",24],["J",28],["K",12],["L",10],["M",18],["N",18],["O",42],["P",20]]) sheet.getRange(`${column}:${column}`).format.columnWidth = width;
sheet.getRange("K5:K6").format.numberFormat = "#,##0.00";
sheet.getRange("N5:N6").format.numberFormat = "yyyy-mm-dd";
sheet.getRange("M5:M200").dataValidation = { rule: { type: "list", values: ["AVAILABLE","PRE_AGREEMENT","ON_MISSION","UNAVAILABLE"] } };
sheet.getRange("P5:P200").dataValidation = { rule: { type: "list", values: ["DRAFT","SUBMITTED","APPROVED","REJECTED"] } };
sheet.freezePanes.freezeRows(4);
workbook.recalculate();
const check = await workbook.inspect({ kind: "table", range: "Experts!A1:P10", include: "values", tableMaxRows: 10, tableMaxCols: 16 });
if (!check.ndjson.includes("Matricule *")) throw new Error("Template validation failed");
const preview = await workbook.render({ sheetName: "Experts", range: "A1:P10", scale: 1, format: "png" });
await fs.writeFile("C:/Users/hamza/Desktop/mvp/.tmp/expert_import_template_preview.png", new Uint8Array(await preview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(output);
