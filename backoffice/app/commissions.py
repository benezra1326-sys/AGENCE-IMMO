"""Calcul indicatif des commissions (brief du 9 novembre 2026). Ne vaut ni négociation ni accord.

- Commission totale d'agence : C.
- Partage entre agences : une agence partenaire qui apporte l'acheteur reçoit en général 50 % de C.
- Apporteur de contact : en général 10 % de C.
- Part d'Avishay : 50 % de ce que reçoit Levy & Goldman après partage éventuel.

Confirmé par Avishay le 9 novembre 2026 : la rémunération de l'apporteur est prise sur la part de l'agence,
pas sur la sienne (sa part = 50 % de ce que reçoit Levy & Goldman, apporteur non déduit).
Toute exception ou tout accord commercial doit lui être soumis.
"""


def calculer(commission_totale, *, agence_partenaire=False, apporteur=False,
             part_partenaire=0.50, part_apporteur=0.10, part_avishay=0.50, apporteur_avant_part=False):
    C = float(commission_totale)
    partenaire = C * part_partenaire if agence_partenaire else 0.0
    recu_agence = C - partenaire
    remun_apporteur = C * part_apporteur if apporteur else 0.0
    base_avishay = recu_agence - remun_apporteur if apporteur_avant_part else recu_agence
    avishay = base_avishay * part_avishay
    return {
        "commission_totale": round(C, 2),
        "agence_partenaire": round(partenaire, 2),
        "recu_levy_goldman": round(recu_agence, 2),
        "apporteur": round(remun_apporteur, 2),
        "part_avishay": round(avishay, 2),
        "reste_levy_goldman": round(recu_agence - remun_apporteur - avishay, 2),
        "hypothese": "apporteur déduit avant la part d'Avishay" if apporteur_avant_part else "apporteur payé sur la part de l'agence",
    }
