// Filtres statut / type de la grille de prix (partagés par les totaux
// bâtiment et programme, pour que les deux portent sur les mêmes lots).
export function matchesLotFilters(lot, filters) {
  const okS = !filters || filters.statut === 'Tous' || lot.statut === filters.statut
  const okT = !filters || filters.type === 'Tous' || lot.type === filters.type
  return okS && okT
}

export function isLotFilterActive(filters) {
  return Boolean(filters) && (filters.statut !== 'Tous' || filters.type !== 'Tous')
}

// Totaux d'une liste de lots. Les prix au m² sont des moyennes PONDÉRÉES
// (somme des prix ÷ somme des SHA) : total ÷ SHA totale de la ligne de
// totaux redonne exactement la moyenne affichée. Même règle dans les
// exports Excel (formules) et PDF (backend).
export function lotTotals(lots) {
  const sum = (field) => lots.reduce((acc, l) => acc + (Number(l[field]) || 0), 0)
  const sha = sum('sha_m2')
  const prixLogement = sum('prix_logement')
  const prixTotal = sum('prix_total')
  return {
    count: lots.length,
    sha,
    prixLogement,
    prixStationnement: sum('prix_stationnement'),
    prixTotal,
    m2Appart: sha > 0 ? prixLogement / sha : null,
    m2StationnementInclus: sha > 0 ? prixTotal / sha : null,
  }
}
