"""Actions d'Avishay, communes au tableau de bord et à Telegram."""
import hashlib

from . import registre, taches
from .db import journaliser, ligne, maintenant


def valider_contenu(cx, cid, canal):
    c = cx.execute("SELECT * FROM contenus WHERE id=?", (cid,)).fetchone()
    if not c:
        return False, f"Contenu {cid} introuvable."
    if c["statut"] == "valide":
        return True, f"« {c['titre']} » était déjà validé."
    cx.execute("UPDATE contenus SET statut='valide', maj_le=? WHERE id=?", (maintenant(), cid))
    cx.execute("INSERT INTO retours (contenu_id, decision, texte, canal, cree_le) VALUES (?,?,?,?,?)",
               (cid, "valide", None, canal, maintenant()))
    journaliser(cx, "avishay", f"contenu validé ({canal})", cid, c["titre"])
    return True, f"Validé : « {c['titre']} ». Rien n'est publié tant que la publication n'est pas activée."


def demander_modification(cx, cid, texte, canal):
    c = cx.execute("SELECT * FROM contenus WHERE id=?", (cid,)).fetchone()
    if not c:
        return False, f"Contenu {cid} introuvable."
    if not texte or not texte.strip():
        return False, "Indique la modification souhaitée."
    t = maintenant()
    cx.execute("UPDATE contenus SET statut='modification_demandee', maj_le=? WHERE id=?", (t, cid))
    cx.execute("INSERT INTO retours (contenu_id, decision, texte, canal, cree_le) VALUES (?,?,?,?,?)",
               (cid, "modification", texte.strip(), canal, t))
    agent = "editorial"
    if c["tache_id"]:
        tache = cx.execute("SELECT agent FROM taches WHERE id=?", (c["tache_id"],)).fetchone()
        agent = tache["agent"] if tache else agent
    empreinte = hashlib.sha1(f"{cid}:{texte.strip()}".encode()).hexdigest()[:8]
    taches.creer(cx, activite=c["activite"], agent=agent, titre=f"Modifier « {c['titre']} » : {texte.strip()[:80]}",
                 cle_unique=f"modif:{cid}:{empreinte}", type="modification_contenu", source=f"Avishay via {canal}",
                 donnees={"contenu_id": cid, "demande": texte.strip()})
    journaliser(cx, "avishay", f"modification demandée ({canal})", cid, texte.strip()[:200])
    return True, f"Modification enregistrée pour « {c['titre']} ». Une tâche a été créée pour l'agent {agent}."


def consigne(cx, texte, canal, message_id=None, agent=None):
    """Une consigne libre devient une tâche : pour l'agent nommé par Avishay, sinon pour la coordination
    qui la répartit (sans doublon si le message est rejoué)."""
    texte = (texte or "").strip()
    if not texte:
        return None, "Consigne vide."
    cle = f"consigne:{canal}:{message_id}" if message_id else "consigne:" + hashlib.sha1(texte.encode()).hexdigest()
    agents_connus = {a["id"] for a in registre.charger_registre()["agents"]} if agent else set()
    destinataire = agent if agent in agents_connus else "coordination"
    t, cree = taches.creer(cx, activite="immo", agent=destinataire, titre=texte[:140], cle_unique=cle,
                           type="consigne", source=f"Avishay via {canal}", donnees={"texte": texte})
    if not cree:
        return t, f"Consigne déjà enregistrée ({t['id']})."
    return t, (f"Consigne enregistrée ({t['id']}). Elle reste en attente tant qu'aucun agent ne tourne sur le serveur ; "
               "elle est visible dans le tableau de bord.")


def contenus_a_valider(cx):
    return [ligne(r) for r in cx.execute("SELECT * FROM contenus WHERE statut='a_valider' ORDER BY date_prevue").fetchall()]
