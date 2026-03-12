# Architecture Decision Records (ADR)

**But:** Documenter les decisions architecturales majeures et leur contexte.

**Pourquoi:** Le code montre le *quoi*, les ADRs expliquent le *pourquoi*. Reduit le bus factor et aide les nouveaux contributeurs a comprendre les choix techniques.

**Comment:** Chaque ADR suit le format: Context, Decision, Consequences (positives/negatives), Alternatives rejetees.

**Structure:**
- `0001-slide-id-md5-path.md` - Schema d'identification des lames
- `0002-optional-modules-try-except.md` - Pattern modules optionnels
- `0003-stateless-tile-server-inmemory-cache.md` - Architecture tile server
- `0004-native-slide-formats-no-dicom-conversion.md` - Formats natifs vs DICOM
- `0005-postgis-annotations.md` - PostGIS pour annotations spatiales
- `0006-mock-data-worklist-strategy.md` - Strategie mock data worklist
