"""
================================================================================
TP 5 : LLM - Découverte pratique d'un LLM avec génération et analyse d'attention
Filière : Masters IADS - M2I, S3 | Automation & Agentic AI
Encadrante : Prof. Imane Lahbari

Pipeline complet :
  Étape 1 : Introduction et préparation (GPT-2)
  Étape 2 : Tokenisation et embeddings (BPE & Cosine Similarity)
  Étape 3 : Génération de texte simple (Logits, Softmax & Stratégies de décodage)
  Étape 4 : Visualisation simplifiée de l'attention (Self-Attention & Heatmaps)
  Étape 5 : Discussion et analyse (Coréférence, Winograd & Bilan théorique)
================================================================================
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Forcer l'encodage UTF-8 sur Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM

# Définition des dossiers
BASE_DIR = Path(__file__).resolve().parent
VIS_DIR = BASE_DIR / "visualisations"
VIS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration de l'affichage Matplotlib
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "figure.titlesize": 14,
})


def print_banner(title: str, step_num: int = None):
    """Affiche une bannière formatée pour délimiter les étapes."""
    separator = "=" * 80
    print(f"\n{separator}")
    if step_num is not None:
        print(f"  ÉTAPE {step_num} : {title.upper()}")
    else:
        print(f"  {title.upper()}")
    print(f"{separator}\n")


def plot_heatmap(
    data: np.ndarray,
    xticklabels: List[str] = None,
    yticklabels: List[str] = None,
    title: str = None,
    xlabel: str = None,
    ylabel: str = None,
    cbar_label: str = None,
    cmap: str = "Blues",
    annot: bool = True,
    fmt: str = ".2f",
    vmin: float = None,
    vmax: float = None,
    ax: plt.Axes = None,
):
    """
    Trace une heatmap professionnelle sans dépendre de Seaborn ni de Pandas,
    évitant tout problème de blocage DLL sur Windows.
    """
    standalone = False
    if ax is None:
        standalone = True
        fig, ax = plt.subplots(figsize=(8, 6.5))
    else:
        fig = ax.figure

    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")

    if cbar_label is not None:
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(cbar_label)

    if xticklabels is not None:
        ax.set_xticks(range(len(xticklabels)))
        ax.set_xticklabels(xticklabels, rotation=45, ha="right", fontsize=9)
    if yticklabels is not None:
        ax.set_yticks(range(len(yticklabels)))
        ax.set_yticklabels(yticklabels, fontsize=9)

    if annot:
        nrows, ncols = data.shape
        val_min = vmin if vmin is not None else float(data.min())
        val_max = vmax if vmax is not None else float(data.max())
        mid = (val_min + val_max) / 2.0
        for i in range(nrows):
            for j in range(ncols):
                val = data[i, j]
                # Choisir une couleur de contraste adaptée
                text_color = "white" if val > mid else "black"
                ax.text(j, i, f"{val:{fmt[1:]}}", ha="center", va="center", color=text_color, fontsize=8)

    if title:
        ax.set_title(title, fontsize=11, pad=10)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)

    if standalone:
        plt.tight_layout()

    return im


# ==============================================================================
# ÉTAPE 1 : Introduction et préparation
# ==============================================================================
def step1_introduction(model_name: str = "gpt2"):
    """
    Présente l'architecture de GPT-2, ses hyperparamètres clés et les dépendances.
    """
    print_banner("Introduction et préparation du modèle LLM", 1)

    print(f"[+] Modèle sélectionné : {model_name}")
    print("[+] Architecture        : Transformer Décodeur seul (Causal Language Model)")
    print("[+] Concepteur          : OpenAI (Radford et al., 2019)")
    print("\nCaractéristiques architecturales de GPT-2 (base) :")
    print("  • Nombre de paramètres       : ~124 millions")
    print("  • Taille du vocabulaire (BPE): 50 257 tokens")
    print("  • Dimension des embeddings (d_model): 768")
    print("  • Nombre de couches (L)      : 12 blocs Transformer")
    print("  • Nombre de têtes par couche : 12 têtes d'attention (d_k = 768 / 12 = 64)")
    print("  • Longueur de contexte max   : 1024 tokens")
    print("  • Mécanisme de masquage      : Masque causal autorégressif (Attention unilatérale gauche-à-droite)")

    print("\nVérification de l'environnement matériel :")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  • Périphérique actif        : {device.upper()}")
    if device == "cuda":
        print(f"  • GPU détecté               : {torch.cuda.get_device_name(0)}")
    else:
        print("  • Mode CPU actif (suffisant et rapide pour GPT-2 base).")

    print("\n[✓] Étape 1 complétée avec succès.\n")


# ==============================================================================
# ÉTAPE 2 : Tokenisation et Embeddings
# ==============================================================================
def step2_tokenization_and_embeddings(
    sentence: str = "Artificial intelligence transforms the modern world.",
    model_name: str = "gpt2"
) -> Tuple[AutoTokenizer, AutoModel, torch.Tensor, List[str]]:
    """
    Démontre la tokenisation BPE et calcule la similarité cosinus entre embeddings.
    """
    print_banner("Tokenisation et Embeddings", 2)

    print(f"[+] Chargement du tokenizer et du modèle pour '{model_name}'...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    print(f"\n[1] Phrase d'entrée à analyser :")
    print(f"    « {sentence} »\n")

    # 1. Tokenisation
    input_ids = tokenizer.encode(sentence, return_tensors="pt")
    token_ids_list = input_ids[0].tolist()
    tokens = [tokenizer.decode([tid]) for tid in token_ids_list]
    raw_tokens = tokenizer.convert_ids_to_tokens(token_ids_list)

    print("[2] Décomposition en Tokens (Byte-Pair Encoding - BPE) :")
    print(f"{'Index':<6} | {'Token ID':<10} | {'Token Brut (BPE)':<18} | {'Token Décodé':<15}")
    print("-" * 55)
    for idx, (tid, raw_tok, dec_tok) in enumerate(zip(token_ids_list, raw_tokens, tokens)):
        print(f"{idx:<6} | {tid:<10} | {raw_tok:<18} | {repr(dec_tok):<15}")

    print("\nObservation :")
    print("  - Le caractère 'Ġ' (Unicode \\u0120) symbolise un espace blanc précédant le sous-mot.")
    print("  - Le BPE permet de fragmenter les mots rares ou composés en sous-unités fréquentes.")

    # 2. Extraction des embeddings
    print("\n[3] Extraction des embeddings statiques (WTE : Word Token Embeddings) :")
    with torch.no_grad():
        token_embeddings = model.wte(input_ids)[0]  # Shape: (seq_len, 768)
        outputs = model(input_ids)
        last_hidden_state = outputs.last_hidden_state[0]  # Shape: (seq_len, 768)

    print(f"  • Forme du tenseur d'embeddings : {token_embeddings.shape} (Longueur séquence: {len(tokens)}, Dimension: {token_embeddings.shape[1]})")

    # 3. Calcul de similarité Cosinus
    print("\n[4] Calcul de la similarité cosinus entre tokens :")
    norm_embeddings = F.normalize(token_embeddings, p=2, dim=-1)
    cos_sim_matrix = torch.mm(norm_embeddings, norm_embeddings.t()).numpy()

    clean_labels = [tok.strip() if tok.strip() else f"[{repr(tok)}]" for tok in tokens]

    plt.figure(figsize=(8, 6.5))
    plot_heatmap(
        cos_sim_matrix,
        xticklabels=clean_labels,
        yticklabels=clean_labels,
        title=f"Similarité Cosinus entre Embeddings Statiques (WTE)\nPhrase: « {sentence} »",
        xlabel="Tokens",
        ylabel="Tokens",
        cbar_label="Similarité Cosinus [-1, 1]",
        cmap="cividis",
        annot=True,
        fmt=".2f",
        vmin=-0.2,
        vmax=1.0
    )
    save_path = VIS_DIR / "01_similarity_embeddings.png"
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  [✓] Graphique sauvegardé dans : {save_path}")

    # Similarité contextualisée (last_hidden_state)
    norm_hidden = F.normalize(last_hidden_state, p=2, dim=-1)
    cos_sim_contextual = torch.mm(norm_hidden, norm_hidden.t()).numpy()

    plt.figure(figsize=(8, 6.5))
    plot_heatmap(
        cos_sim_contextual,
        xticklabels=clean_labels,
        yticklabels=clean_labels,
        title=f"Similarité Cosinus des Représentations Contextualisées (Couche 12)\nPhrase: « {sentence} »",
        xlabel="Tokens",
        ylabel="Tokens",
        cbar_label="Similarité Cosinus (Contextuelle)",
        cmap="viridis",
        annot=True,
        fmt=".2f",
        vmin=-0.2,
        vmax=1.0
    )
    save_path_ctx = VIS_DIR / "01_similarity_contextual.png"
    plt.savefig(save_path_ctx, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  [✓] Graphique contextualisé sauvegardé dans : {save_path_ctx}")

    print("\n[✓] Étape 2 complétée avec succès.\n")
    return tokenizer, model, input_ids, tokens


# ==============================================================================
# ÉTAPE 3 : Génération de texte simple & analyse des probabilités
# ==============================================================================
def step3_text_generation_and_probabilities(
    prompt: str = "The future of artificial intelligence is",
    model_name: str = "gpt2",
    max_new_tokens: int = 30
):
    """
    Montre comment le LLM calcule les logits, produit une distribution de probabilités,
    et génère la suite selon plusieurs stratégies de décodage.
    """
    print_banner("Génération de texte et sélection des tokens", 3)

    print(f"[+] Chargement de AutoModelForCausalLM ('{model_name}')...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    causal_model = AutoModelForCausalLM.from_pretrained(model_name)
    causal_model.eval()

    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs["input_ids"]

    print(f"\n[1] Prompt de départ : « {prompt} »")

    # 1. Forward pass pour inspecter les logits du token suivant
    with torch.no_grad():
        outputs = causal_model(**inputs)
        logits = outputs.logits  # Shape: (1, seq_len, vocab_size)

    next_token_logits = logits[0, -1, :]  # Logits pour la position suivante (50257,)
    probs = F.softmax(next_token_logits, dim=-1)

    # Récupérer les top-10 candidats
    top_k = 10
    top_probs, top_indices = torch.topk(probs, k=top_k)
    top_probs = top_probs.tolist()
    top_indices = top_indices.tolist()

    print(f"\n[2] Top {top_k} des tokens prédits pour succéder à « {prompt} » :")
    print(f"{'Rang':<5} | {'Token ID':<10} | {'Token Décodé':<18} | {'Logit':<10} | {'Probabilité (%)':<15}")
    print("-" * 65)

    top_tokens_labels = []
    for rank, (tid, prob) in enumerate(zip(top_indices, top_probs), start=1):
        token_str = tokenizer.decode([tid])
        logit_val = next_token_logits[tid].item()
        top_tokens_labels.append(repr(token_str))
        print(f"{rank:<5} | {tid:<10} | {repr(token_str):<18} | {logit_val:<10.2f} | {prob * 100:<15.2f}%")

    # Graphique barres des probabilités
    plt.figure(figsize=(9, 4.5))
    bars = plt.barh(top_tokens_labels[::-1], [p * 100 for p in top_probs[::-1]], color="#2b5c8f")
    plt.xlabel("Probabilité (%)")
    plt.title(f"Top {top_k} des Tokens Suivants pour le Prompt :\n« {prompt} »", fontsize=11)

    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.3, bar.get_y() + bar.get_height() / 2, f"{width:.2f}%", 
                 va="center", ha="left", fontsize=9, color="#222222")

    plt.xlim(0, max(top_probs) * 100 + 5)
    plt.tight_layout()
    save_path = VIS_DIR / "02_next_token_probs.png"
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"\n  [✓] Graphique sauvegardé dans : {save_path}")

    # 2. Démonstration des stratégies de décodage
    print("\n[3] Génération de complétion avec différentes stratégies de décodage :\n")
    torch.manual_seed(42)

    # A. Greedy Search
    greedy_ids = causal_model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )
    print("A. Greedy Search (Déterministe - Choix du token max à chaque pas) :")
    print(f"   « {tokenizer.decode(greedy_ids[0], skip_special_tokens=True)} »\n")

    # B. Temperature Sampling (T = 0.7)
    sample_temp_ids = causal_model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id
    )
    print("B. Sampling avec Température (T = 0.7 - Équilibre cohérence/créativité) :")
    print(f"   « {tokenizer.decode(sample_temp_ids[0], skip_special_tokens=True)} »\n")

    # C. Top-K Sampling (k = 50)
    topk_ids = causal_model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        top_k=50,
        temperature=0.8,
        pad_token_id=tokenizer.eos_token_id
    )
    print("C. Top-K Sampling (k = 50, T = 0.8 - Tronque la queue de distribution) :")
    print(f"   « {tokenizer.decode(topk_ids[0], skip_special_tokens=True)} »\n")

    # D. Top-P (Nucleus) Sampling (p = 0.90)
    topp_ids = causal_model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        top_p=0.90,
        temperature=0.8,
        pad_token_id=tokenizer.eos_token_id
    )
    print("D. Top-P / Nucleus Sampling (p = 0.90, T = 0.8 - Sélection adaptative) :")
    print(f"   « {tokenizer.decode(topp_ids[0], skip_special_tokens=True)} »\n")

    print("[✓] Étape 3 complétée avec succès.\n")


# ==============================================================================
# ÉTAPE 4 : Visualisation simplifiée de l'attention
# ==============================================================================
def step4_attention_visualization(
    sentence: str = "The cat sat on the mat because it was tired",
    model_name: str = "gpt2"
):
    """
    Extrait les poids d'attention multi-têtes et génère des heatmaps explicatives.
    """
    print_banner("Visualisation Simplifiée de l'Attention", 4)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, output_attentions=True)
    model.eval()

    inputs = tokenizer(sentence, return_tensors="pt")
    input_ids = inputs["input_ids"]
    token_ids_list = input_ids[0].tolist()
    tokens = [tokenizer.decode([tid]) for tid in token_ids_list]
    clean_tokens = [tok.strip() if tok.strip() else f"[{repr(tok)}]" for tok in tokens]

    print(f"[1] Phrase analysée : « {sentence} »")
    print(f"[2] Nombre de tokens : {len(tokens)}")

    # Extraction des poids d'attention
    with torch.no_grad():
        outputs = model(**inputs, output_attentions=True)
        attentions = outputs.attentions

    num_layers = len(attentions)
    num_heads = attentions[0].shape[1]
    seq_len = len(tokens)

    print(f"[3] Structure des tenseurs d'attention :")
    print(f"    • Nombre de couches Transformer (L) : {num_layers}")
    print(f"    • Nombre de têtes par couche (H)   : {num_heads}")
    print(f"    • Dimension de chaque matrice       : ({seq_len}, {seq_len})")

    # 1. Visualisation : Moyenne des 12 têtes de la dernière couche (Couche 11)
    last_layer_att = attentions[-1][0]  # Shape: (12, seq_len, seq_len)
    avg_attention_last_layer = last_layer_att.mean(dim=0).numpy()

    plt.figure(figsize=(8.5, 7))
    plot_heatmap(
        avg_attention_last_layer,
        xticklabels=clean_tokens,
        yticklabels=clean_tokens,
        title=f"Matrice d'Attention - Dernière Couche (Layer 12, Moyenne des 12 Têtes)\n« {sentence} »",
        xlabel="Tokens Clés / Regardés (Keys)",
        ylabel="Tokens Requêtes (Queries)",
        cbar_label="Poids d'attention (Moyenne des têtes)",
        cmap="Blues",
        annot=True,
        fmt=".2f"
    )
    save_path_avg = VIS_DIR / "03_attention_layer11_avg.png"
    plt.savefig(save_path_avg, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"\n  [✓] Heatmap moyenne sauvegardée dans : {save_path_avg}")

    # 2. Visualisation : Grille complète des 12 têtes d'une couche intermédiaire (Couche 8)
    chosen_layer = 7  # 8ème couche (0-indexée)
    layer_att = attentions[chosen_layer][0].numpy()  # (12, seq_len, seq_len)

    fig, axes = plt.subplots(3, 4, figsize=(16, 12), sharex=True, sharey=True)
    for head_idx in range(num_heads):
        ax = axes[head_idx // 4, head_idx % 4]
        plot_heatmap(
            layer_att[head_idx],
            xticklabels=clean_tokens,
            yticklabels=clean_tokens,
            title=f"Couche {chosen_layer+1} - Tête {head_idx+1}",
            cmap="viridis",
            annot=False,
            ax=ax
        )

    fig.suptitle(f"Spécialisation des 12 Têtes d'Attention (Couche {chosen_layer+1})\n« {sentence} »", fontsize=14)
    plt.tight_layout()
    save_path_grid = VIS_DIR / "04_attention_heads_grid.png"
    plt.savefig(save_path_grid, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  [✓] Grille multi-têtes sauvegardée dans : {save_path_grid}")

    print("\nObservation fondamentale sur le masquage causal :")
    print("  - Observez le triangle supérieur droit : tous les coefficients au-dessus de la diagonale valent 0.00.")
    print("  - Cela démontre mathématiquement le masquage causal autorégressif : le token à la position i")
    print("    ne peut jamais prêter attention aux tokens futurs (j > i).")

    print("\n[✓] Étape 4 complétée avec succès.\n")


# ==============================================================================
# ÉTAPE 5 : Discussion et Analyse Comparée (Coréférences & Théorie)
# ==============================================================================
def step5_discussion_and_analysis(model_name: str = "gpt2"):
    """
    Compare l'attention sur des paires de phrases de Winograd Schema pour illustrer
    la résolution de coréférence pronominale et fait le lien avec la théorie.
    """
    print_banner("Discussion et Analyse Approfondie", 5)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, output_attentions=True)
    model.eval()

    # Paire classique de phrases de Winograd
    phrase_a = "The animal didn't cross the street because it was too tired"
    phrase_b = "The animal didn't cross the street because it was too wide"

    print("[1] Test de coréférence pronominale (Schémas de Winograd) :")
    print(f"    Phrase A : « {phrase_a} »")
    print(f"    Phrase B : « {phrase_b} »")
    print("\nQuestion théorique : Le pronom 'it' regarde-t-il 'animal' (si tired) ou 'street' (si wide) ?\n")

    def get_attention_for_sentence(s: str):
        inputs = tokenizer(s, return_tensors="pt")
        tokens = [tokenizer.decode([tid]) for tid in inputs["input_ids"][0].tolist()]
        clean = [tok.strip() if tok.strip() else f"[{repr(tok)}]" for tok in tokens]
        with torch.no_grad():
            outputs = model(**inputs, output_attentions=True)
        return clean, outputs.attentions

    tokens_a, atts_a = get_attention_for_sentence(phrase_a)
    tokens_b, atts_b = get_attention_for_sentence(phrase_b)

    def find_it_index(tok_list):
        for i, t in enumerate(tok_list):
            if "it" in t.lower():
                return i
        return -1

    idx_it_a = find_it_index(tokens_a)
    idx_it_b = find_it_index(tokens_b)

    print(f"  • Index du token 'it' dans Phrase A : {idx_it_a} ('{tokens_a[idx_it_a]}')")
    print(f"  • Index du token 'it' dans Phrase B : {idx_it_b} ('{tokens_b[idx_it_b]}')")

    target_layer = 10  # Couche 11
    att_it_a = atts_a[target_layer][0].mean(dim=0)[idx_it_a].numpy()
    att_it_b = atts_b[target_layer][0].mean(dim=0)[idx_it_b].numpy()

    # Visualisation comparative pure Matplotlib
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    x_a = tokens_a[:idx_it_a + 1]
    y_a = att_it_a[:idx_it_a + 1]
    colors_a = plt.cm.magma(np.linspace(0.3, 0.85, len(x_a)))
    ax1.bar(range(len(x_a)), y_a, color=colors_a, edgecolor="#222222", linewidth=0.7)
    ax1.set_xticks(range(len(x_a)))
    ax1.set_xticklabels(x_a, rotation=45, ha="right")
    ax1.set_title("Phrase A : « ... because it was too tired »\nAttention du token 'it'", fontsize=11)
    ax1.set_ylabel("Poids d'attention moyen (Couche 11)")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    x_b = tokens_b[:idx_it_b + 1]
    y_b = att_it_b[:idx_it_b + 1]
    colors_b = plt.cm.viridis(np.linspace(0.3, 0.85, len(x_b)))
    ax2.bar(range(len(x_b)), y_b, color=colors_b, edgecolor="#222222", linewidth=0.7)
    ax2.set_xticks(range(len(x_b)))
    ax2.set_xticklabels(x_b, rotation=45, ha="right")
    ax2.set_title("Phrase B : « ... because it was too wide »\nAttention du token 'it'", fontsize=11)
    ax2.set_ylabel("Poids d'attention moyen (Couche 11)")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    save_path_cor = VIS_DIR / "05_coreference_attention.png"
    plt.savefig(save_path_cor, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"\n  [✓] Comparaison de coréférence sauvegardée dans : {save_path_cor}")

    # Bilan théorique synthétique
    print("\n[2] Synthèse Théorique du Pipeline LLM :")
    print("  1. Tokenisation (BPE) :")
    print("     - Réduit la combinatoire du vocabulaire (ici 50 257) tout en évitant les mots hors-vocabulaire.")
    print("     - Permet une flexibilité multi-langue et une gestion compacte des racines lexicales.")
    print("  2. Embeddings (Statique vs Contextuel) :")
    print("     - WTE fournit un point de départ sémantique invariable.")
    print("     - WPE injecte la notion d'ordre séquentiel (cruciale car l'attention pure est invariante par permutation).")
    print("     - Les couches Transformer affinent ces vecteurs pour créer des représentations hautement contextualisées.")
    print("  3. Self-Attention & Masque Causal :")
    print("     - La formule Softmax(QK^T / sqrt(d_k) + M)V permet à chaque token d'interroger dynamiquement son contexte passé.")
    print("     - Le masque causal M garantit le respect de la flèche du temps (pas de fuite vers le futur).")
    print("  4. Génération Auto-régressive :")
    print("     - Le modèle prédit un unique token à chaque passage avant de le concaténer à l'entrée.")
    print("     - Le compromis entre Greedy Search (déterministe mais répétitif) et Sampling (température, top-k, top-p)")
    print("       conditionne la qualité, la diversité et la véracité du texte généré.")

    print("\n[✓] Étape 5 complétée avec succès.\n")


# ==============================================================================
# POINT D'ENTRÉE PRINCIPAL (CLI)
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="TP 5 : Découverte pratique d'un LLM avec génération et analyse d'attention."
    )
    parser.add_argument(
        "--step",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Exécuter une étape spécifique (1 à 5). Par défaut, toutes les étapes sont exécutées."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt2",
        help="Nom du modèle Hugging Face pré-entraîné à utiliser (défaut : 'gpt2')."
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="The future of artificial intelligence is",
        help="Phrase ou prompt de départ pour la génération de texte (étape 3)."
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=30,
        help="Nombre maximal de nouveaux tokens à générer (défaut : 30)."
    )
    args = parser.parse_args()

    print("\n" + "#" * 80)
    print("  TP 5 - DÉCOUVERTE PRATIQUE D'UN LLM (GPT-2)")
    print("  Génération, Embeddings, Similarité & Mécanisme de Self-Attention")
    print("#" * 80)

    if args.step == 1:
        step1_introduction(args.model)
    elif args.step == 2:
        step2_tokenization_and_embeddings(model_name=args.model)
    elif args.step == 3:
        step3_text_generation_and_probabilities(prompt=args.prompt, model_name=args.model, max_new_tokens=args.max_tokens)
    elif args.step == 4:
        step4_attention_visualization(model_name=args.model)
    elif args.step == 5:
        step5_discussion_and_analysis(model_name=args.model)
    else:
        # Exécution intégrale
        step1_introduction(args.model)
        step2_tokenization_and_embeddings(model_name=args.model)
        step3_text_generation_and_probabilities(prompt=args.prompt, model_name=args.model, max_new_tokens=args.max_tokens)
        step4_attention_visualization(model_name=args.model)
        step5_discussion_and_analysis(model_name=args.model)

        print("\n" + "=" * 80)
        print("  [SUCCESS] TOUTES LES ÉTAPES DU TP 5 ONT ÉTÉ EXÉCUTÉES AVEC SUCCÈS !")
        print(f"  Consultez les visualisations générées dans : {VIS_DIR}")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
