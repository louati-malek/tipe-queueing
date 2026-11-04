# Original TIPE code (MP, 2024/2025), reconstructed from the annex of TIPE.pdf.
# Kept unchanged on purpose, as a record of the original work. Only two things differ
# from the PDF: the Greek variable "ρ" (lost in PDF text extraction) is written `rho`,
# and plt.show() calls are left as they were. See README "What was corrected" for the
# issues found in this version; the corrected code lives in the `queueing/` package.
import numpy as np
import matplotlib.pyplot as plt
from queue import Queue
import random
import math
random.seed(42)
taux_service = 1 / 300
capacite_max = 10
duree_simulation = 8 * 3600
serveurs_1, serveurs_3, serveurs_6 = 1, 3, 6
taux_occupation = np.linspace(0.1, 0.99, 200)

scenarios = {
    "Cas faible": {"taux_arrivee": 1 / 900, "couleur": "green"},
    "Cas moyen": {"taux_arrivee": 1 / 450, "couleur": "blue"},
    "Cas saturé": {"taux_arrivee": 1 / 250, "couleur": "red"}
}


def simuler_mm1(taux_arrivee, taux_service, duree, capacite_max=None):
    temps = 0
    file_attente = Queue()
    serveur_occupe = False
    prochaine_arrivee = random.expovariate(taux_arrivee)
    prochain_depart = float('inf')
    temps_attente, longueurs_file = [], []
    perdus, arrives = 0, 0
    while temps < duree:
        temps = min(prochaine_arrivee, prochain_depart)
        etat_actuel = file_attente.qsize() + int(serveur_occupe)
        longueurs_file.append(file_attente.qsize())
        if temps == prochaine_arrivee:
            arrives += 1
            if capacite_max is not None and etat_actuel >= capacite_max:
                perdus += 1
            elif serveur_occupe:
                file_attente.put(temps)
            else:
                serveur_occupe = True
                prochain_depart = temps + random.expovariate(taux_service)
            prochaine_arrivee = temps + random.expovariate(taux_arrivee)
        elif temps == prochain_depart:
            if not file_attente.empty():
                arrivee = file_attente.get()
                temps_attente.append(temps - arrivee)
                prochain_depart = temps + random.expovariate(taux_service)
            else:
                serveur_occupe = False
                prochain_depart = float('inf')
    return temps_attente, longueurs_file


def simuler_mmc(taux_arrivee, taux_service, nb_serveurs, duree, capacite_max=None):
    temps = 0
    file_attente = Queue()
    prochaine_arrivee = random.expovariate(taux_arrivee)
    prochains_departs = [float('inf')] * nb_serveurs
    temps_attente, longueurs_file = [], []
    perdus, arrives = 0, 0
    while temps < duree:
        temps = min([prochaine_arrivee] + prochains_departs)
        nb_occupe = sum(d != float('inf') for d in prochains_departs)
        etat_actuel = file_attente.qsize() + nb_occupe
        longueurs_file.append(file_attente.qsize())
        if temps == prochaine_arrivee:
            arrives += 1
            if capacite_max and etat_actuel >= capacite_max:
                perdus += 1
            else:
                try:
                    i = prochains_departs.index(float('inf'))
                    prochains_departs[i] = temps + random.expovariate(taux_service)
                except ValueError:
                    file_attente.put(temps)
            prochaine_arrivee = temps + random.expovariate(taux_arrivee)
        else:
            i = prochains_departs.index(temps)
            if not file_attente.empty():
                arrivee = file_attente.get()
                temps_attente.append(temps - arrivee)
                prochains_departs[i] = temps + random.expovariate(taux_service)
            else:
                prochains_departs[i] = float('inf')
    return temps_attente, longueurs_file


def metriques_mm1(rho, taux_service):
    taux_arrivee = rho * taux_service
    if taux_arrivee < taux_service:
        W = 1 / (taux_service - taux_arrivee)
        L = taux_arrivee / (taux_service - taux_arrivee)
    else:
        W, L = float('inf'), float('inf')
    return W, L


def metriques_mmc(rho, nb_serveurs, taux_service):
    taux_arrivee = rho * nb_serveurs * taux_service
    r = taux_arrivee / taux_service
    somme = sum((r ** n) / math.factorial(n) for n in range(nb_serveurs))
    dernier_terme = (r ** nb_serveurs) / (math.factorial(nb_serveurs) * (1 - rho))
    P0 = 1 / (somme + dernier_terme)
    Pq = dernier_terme * P0
    Lq = Pq * rho / (1 - rho)
    L = Lq + r
    W = L / taux_arrivee
    return W, L


if __name__ == "__main__":
    W_mm1, L_mm1 = [], []
    W_mm3, L_mm3 = [], []
    W_mm6, L_mm6 = [], []
    for rho in taux_occupation:
        W, L = metriques_mm1(rho, taux_service)
        W_mm1.append(W); L_mm1.append(L)
        if rho >= 1:
            W_mm3.append(float('nan')); L_mm3.append(float('nan'))
            W_mm6.append(float('nan')); L_mm6.append(float('nan'))
        else:
            W, L = metriques_mmc(rho, serveurs_3, taux_service)
            W_mm3.append(W); L_mm3.append(L)
            W, L = metriques_mmc(rho, serveurs_6, taux_service)
            W_mm6.append(W); L_mm6.append(L)

    resultats_attente = {"mm1": {}, "mm3": {}, "mm6": {}}
    resultats_file = {"mm1": {}, "mm3": {}, "mm6": {}}
    for nom, params in scenarios.items():
        taux_arrivee = params["taux_arrivee"]
        resultats_attente["mm1"][nom], resultats_file["mm1"][nom] = simuler_mm1(
            taux_arrivee, taux_service, duree_simulation, capacite_max)
        resultats_attente["mm3"][nom], resultats_file["mm3"][nom] = simuler_mmc(
            taux_arrivee, taux_service, serveurs_3, duree_simulation, capacite_max)
        resultats_attente["mm6"][nom], resultats_file["mm6"][nom] = simuler_mmc(
            taux_arrivee, taux_service, serveurs_6, duree_simulation, capacite_max)

    plt.figure(figsize=(12, 6))
    plt.plot(taux_occupation, W_mm1, label="M/M/1", color="red")
    plt.plot(taux_occupation, W_mm3, label="M/M/3", color="blue")
    plt.plot(taux_occupation, W_mm6, label="M/M/6", color="green")
    plt.title("Temps moyen dans le système W(rho)")
    plt.xlabel("rho (Taux d'occupation)"); plt.ylabel("W (secondes)")
    plt.legend(); plt.grid(True); plt.ylim(0, 10000); plt.tight_layout(); plt.show()
