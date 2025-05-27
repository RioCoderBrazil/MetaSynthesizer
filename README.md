# MetaSynthesizer

Ein Tool zur Analyse und Kategorisierung von Prüfberichten anhand farbcodierter Abschnitte.

## Überblick

Dieses Projekt extrahiert farbcodierte Abschnitte aus Word-Dokumenten und kategorisiert die Inhalte nach 23 verschiedenen Kategorien.

## Farbcodierung

- 🟢 GRÜN (#00FF00): Feststellungen (Findings) - Hauptinhalte der Berichte (~40% der Inhalte)
- 🔵 BLAU (#0000FF): Beurteilungen (Evaluation) - Bewertungen der Prüfer
- 🟡 GELB (#FFFF00): Einleitungen (Introduction) - Hintergrund, Methoden, Prüffragen
- 🟣 MAGENTA/ROSA (#FF00FF): Stellungnahmen (Response) - Antworten der geprüften Stellen
- 🟠 DUNKELGELB (#FF8C00): Empfehlungen (Recommendations) - Vorschläge der Prüfer
- ⚫ GRAU (#808080): Anhänge (Appendix) - Zusatzmaterial und Referenzen
- 🔷 TÜRKIS/CYAN (#00FFFF): WIK (Wesentliches in Kürze) - Zusammenfassungen und Kernaussagen
