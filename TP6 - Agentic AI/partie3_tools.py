"""
Partie 3 : Création de Tools
Questions 8, 9, 10, 11 :
- Tool 'addition' qui calcule la somme de deux nombres
- Tool 'celsius_to_fahrenheit' pour convertir les températures
- Descriptions claires pour chaque tool
- Tests unitaires / séparés des outils
"""

from langchain.tools import tool

# 8 & 11. Outil d'addition avec description claire
@tool
def addition(a: float, b: float) -> float:
    """Calcule la somme de deux nombres a et b. Utile pour faire des additions arithmétiques."""
    return float(a) + float(b)

# 10 & 11. Outil de conversion Celsius vers Fahrenheit avec description claire
@tool
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convertit une température exprimée en degrés Celsius (°C) vers Fahrenheit (°F).
    Formule utilisée : (celsius * 9/5) + 32."""
    return (float(celsius) * 9.0 / 5.0) + 32.0

def run_partie3():
    print("=" * 60)
    print("Partie 3 : Test séparé des Tools")
    print("=" * 60)

    # 9. Test séparé du Tool addition
    print("\n--- Test 1 : Tool addition ---")
    val_a, val_b = 12.5, 7.5
    res_add = addition.invoke({"a": val_a, "b": val_b})
    print(f"Tool name: {addition.name}")
    print(f"Tool description: {addition.description}")
    print(f"Addition({val_a}, {val_b}) = {res_add}")
    assert res_add == 20.0, "Erreur dans le test d'addition"

    # Test du Tool celsius_to_fahrenheit
    print("\n--- Test 2 : Tool celsius_to_fahrenheit ---")
    deg_c = 25.0
    res_f = celsius_to_fahrenheit.invoke({"celsius": deg_c})
    print(f"Tool name: {celsius_to_fahrenheit.name}")
    print(f"Tool description: {celsius_to_fahrenheit.description}")
    print(f"celsius_to_fahrenheit({deg_c}°C) = {res_f}°F")
    assert res_f == 77.0, "Erreur dans le test de conversion Celsius -> Fahrenheit"

    print("\n[SUCCÈS] Tous les tests de Tools ont réussi avec succès !")

if __name__ == "__main__":
    run_partie3()

