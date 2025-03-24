import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import mysql.connector
from mysql.connector import Error
import pandas as pd

class ElectricityConsumptionApp:
 def __init__(self, root):
 self.root = root
 self.root.title("Suivi de Consommation Électrique")
 self.root.geometry("1000x650")
 self.root.configure(bg="#f0f0f0")

 # Configuration de la base de données
 self.db_config = {
 "host": "localhost",
 "user": "root",
 "password": "", # À remplacer par votre mot de passe
 "database": "electricity_consumption"
 }

 # Initialisation de la base de données
 self.initialize_database()

 # Création des onglets
 self.tab_control = ttk.Notebook(root)

 self.tab_monthly = ttk.Frame(self.tab_control)
 self.tab_appliances = ttk.Frame(self.tab_control)
 self.tab_services = ttk.Frame(self.tab_control)
 self.tab_analysis = ttk.Frame(self.tab_control)

 self.tab_control.add(self.tab_monthly, text="Consommation Mensuelle")
 self.tab_control.add(self.tab_appliances, text="Appareils")
 self.tab_control.add(self.tab_services, text="Services")
 self.tab_control.add(self.tab_analysis, text="Analyse & Prédictions")

 self.tab_control.pack(expand=1, fill="both")

 # Définition des catégories d'appareils
 self.appliance_categories = ["PC", "Serveur", "Électroménager", "Éclairage", "Chauffage", "Multimédia", "Autre"]

 # Configuration des onglets
 self.setup_monthly_tab()
 self.setup_appliances_tab()
 self.setup_services_tab()
 self.setup_analysis_tab()

 def initialize_database(self):
 """Initialise la base de données et les tables si elles n'existent pas"""
 try:
 # Connexion sans spécifier de base de données
 connection = mysql.connector.connect(
 host=self.db_config["host"],
 user=self.db_config["user"],
 password=self.db_config["password"]
 )

 cursor = connection.cursor()

 # Création de la base de données si elle n'existe pas
 cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']}")

 # Utilisation de la base de données
 cursor.execute(f"USE {self.db_config['database']}")

 # Création de la table des consommations mensuelles
 cursor.execute("""
 CREATE TABLE IF NOT EXISTS monthly_consumption (
 id INT AUTO_INCREMENT PRIMARY KEY,
 month VARCHAR(50) NOT NULL,
 consumption FLOAT NOT NULL
 )
 """)

 # Création de la table des appareils avec catégorie
 cursor.execute("""
 CREATE TABLE IF NOT EXISTS appliances (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 category VARCHAR(50) NOT NULL,
 power FLOAT NOT NULL,
 usage_hours FLOAT NOT NULL,
 description TEXT
 )
 """)

 # Création de la table des services
 cursor.execute("""
 CREATE TABLE IF NOT EXISTS services (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 appliance_id INT NOT NULL,
 power_overhead FLOAT DEFAULT 0,
 description TEXT,
 FOREIGN KEY (appliance_id) REFERENCES appliances(id) ON DELETE CASCADE
 )
 """)

 connection.commit()

 except Error as e:
 messagebox.showerror("Erreur de Base de Données", f"Erreur lors de l'initialisation: {e}")
 finally:
 if connection.is_connected():
 cursor.close()
 connection.close()

 def execute_query(self, query, params=None, fetch=False):
 """Exécute une requête SQL et retourne les résultats si fetch=True"""
 try:
 connection = mysql.connector.connect(**self.db_config)
 cursor = connection.cursor()

 cursor.execute(query, params or ())

 result = None
 if fetch:
 result = cursor.fetchall()
 else:
 connection.commit()

 return result
 except Error as e:
 messagebox.showerror("Erreur de Base de Données", f"Erreur lors de l'exécution de la requête: {e}")
 return None
 finally:
 if connection.is_connected():
 cursor.close()
 connection.close()

 # Onglet Consommation Mensuelle
 def setup_monthly_tab(self):
 frame = ttk.Frame(self.tab_monthly, padding=20)
 frame.pack(fill="both", expand=True)

 # Formulaire d'ajout
 ttk.Label(frame, text="Ajouter/Modifier la Consommation Mensuelle", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")

 ttk.Label(frame, text="Mois (ex: Janvier 2025):").grid(row=1, column=0, pady=5, sticky="w")
 self.month_entry = ttk.Entry(frame, width=30)
 self.month_entry.grid(row=1, column=1, pady=5, padx=5, sticky="w")

 ttk.Label(frame, text="Consommation (kWh):").grid(row=2, column=0, pady=5, sticky="w")
 self.consumption_entry = ttk.Entry(frame, width=30)
 self.consumption_entry.grid(row=2, column=1, pady=5, padx=5, sticky="w")

 # Boutons
 button_frame = ttk.Frame(frame)
 button_frame.grid(row=3, column=0, columnspan=2, pady=10)

 ttk.Button(button_frame, text="Ajouter", command=self.add_month).pack(side="left", padx=5)
 ttk.Button(button_frame, text="Modifier", command=self.modify_month).pack(side="left", padx=5)

 # Tableau des données
 ttk.Label(frame, text="Consommation Enregistrée", font=("Arial", 12, "bold")).grid(row=4, column=0, columnspan=2, pady=10, sticky="w")

 # Création du treeview (tableau)
 self.monthly_tree = ttk.Treeview(frame, columns=("month", "consumption"), show="headings", height=10)
 self.monthly_tree.grid(row=5, column=0, columnspan=2, sticky="nsew")

 # Configuration des colonnes
 self.monthly_tree.heading("month", text="Mois")
 self.monthly_tree.heading("consumption", text="Consommation (kWh)")
 self.monthly_tree.column("month", width=200)
 self.monthly_tree.column("consumption", width=200)

 # Scrollbar
 scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.monthly_tree.yview)
 scrollbar.grid(row=5, column=2, sticky="ns")
 self.monthly_tree.configure(yscrollcommand=scrollbar.set)

 # Gestion de l'événement de sélection
 self.monthly_tree.bind("<<TreeviewSelect>>", self.on_monthly_select)

 # Chargement des données
 self.load_monthly_data()

 # Configurer le redimensionnement
 frame.columnconfigure(1, weight=1)
 frame.rowconfigure(5, weight=1)

 def load_monthly_data(self):
 """Charge les données mensuelles depuis la base de données"""
 # Effacer le tableau
 for item in self.monthly_tree.get_children():
 self.monthly_tree.delete(item)

 # Charger les données
 query = "SELECT month, consumption FROM monthly_consumption ORDER BY id DESC"
 data = self.execute_query(query, fetch=True)

 if data:
 for row in data:
 self.monthly_tree.insert("", "end", values=row)

 def add_month(self):
 """Ajoute un nouveau mois dans la base de données"""
 month = self.month_entry.get().strip()
 consumption_str = self.consumption_entry.get().strip()

 if not month or not consumption_str:
 messagebox.showwarning("Champs Manquants", "Veuillez remplir tous les champs.")
 return

 try:
 consumption = float(consumption_str)
 except ValueError:
 messagebox.showwarning("Erreur de Format", "La consommation doit être un nombre.")
 return

 # Vérifier si le mois existe déjà
 query = "SELECT id FROM monthly_consumption WHERE month = %s"
 result = self.execute_query(query, (month,), fetch=True)

 if result:
 response = messagebox.askyesno("Mois Existant", f"Le mois '{month}' existe déjà. Voulez-vous mettre à jour sa valeur?")
 if response:
 self.modify_month(forced_month=month, forced_consumption=consumption)
 else:
 # Ajouter le nouveau mois
 query = "INSERT INTO monthly_consumption (month, consumption) VALUES (%s, %s)"
 self.execute_query(query, (month, consumption))
 messagebox.showinfo("Succès", "Données ajoutées avec succès.")

 # Effacer les champs
 self.month_entry.delete(0, tk.END)
 self.consumption_entry.delete(0, tk.END)

 # Recharger les données
 self.load_monthly_data()

 def modify_month(self, forced_month=None, forced_consumption=None):
 """Modifie un mois existant"""
 if forced_month:
 month = forced_month
 consumption = forced_consumption
 else:
 # Obtenir la sélection actuelle
 selection = self.monthly_tree.selection()
 if not selection:
 messagebox.showwarning("Sélection Requise", "Veuillez sélectionner un mois à modifier ou utiliser le formulaire.")
 return

 month = self.month_entry.get().strip()
 consumption_str = self.consumption_entry.get().strip()

 if not month or not consumption_str:
 messagebox.showwarning("Champs Manquants", "Veuillez remplir tous les champs.")
 return

 try:
 consumption = float(consumption_str)
 except ValueError:
 messagebox.showwarning("Erreur de Format", "La consommation doit être un nombre.")
 return

 # Mettre à jour la base de données
 query = "UPDATE monthly_consumption SET consumption = %s WHERE month = %s"
 self.execute_query(query, (consumption, month))
 messagebox.showinfo("Succès", "Données mises à jour avec succès.")

 # Effacer les champs
 self.month_entry.delete(0, tk.END)
 self.consumption_entry.delete(0, tk.END)

 # Recharger les données
 self.load_monthly_data()

 def on_monthly_select(self, event):
 """Remplit les champs lorsqu'un élément est sélectionné dans le tableau"""
 selection = self.monthly_tree.selection()
 if selection:
 item = self.monthly_tree.item(selection[0])
 month, consumption = item["values"]

 # Mettre à jour les champs
 self.month_entry.delete(0, tk.END)
 self.month_entry.insert(0, month)

 self.consumption_entry.delete(0, tk.END)
 self.consumption_entry.insert(0, str(consumption))

 # Onglet Appareils
 def setup_appliances_tab(self):
 frame = ttk.Frame(self.tab_appliances, padding=20)
 frame.pack(fill="both", expand=True)

 # Formulaire d'ajout
 ttk.Label(frame, text="Ajouter un Appareil", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")

 ttk.Label(frame, text="Nom de l'appareil:").grid(row=1, column=0, pady=5, sticky="w")
 self.appliance_name_entry = ttk.Entry(frame, width=30)
 self.appliance_name_entry.grid(row=1, column=1, pady=5, padx=5, sticky="w")

 ttk.Label(frame, text="Catégorie:").grid(row=2, column=0, pady=5, sticky="w")
 self.category_var = tk.StringVar()
 self.category_combobox = ttk.Combobox(frame, textvariable=self.category_var, width=28, state="readonly")
 self.category_combobox['values'] = self.appliance_categories
 self.category_combobox.current(0) # Sélectionne la première catégorie par défaut
 self.category_combobox.grid(row=2, column=1, pady=5, padx=5, sticky="w")

 ttk.Label(frame, text="Puissance (W):").grid(row=3, column=0, pady=5, sticky="w")
 self.power_entry = ttk.Entry(frame, width=30)
 self.power_entry.grid(row=3, column=1, pady=5, padx=5, sticky="w")

 ttk.Label(frame, text="Utilisation (h/jour):").grid(row=4, column=0, pady=5, sticky="w")
 self.usage_entry = ttk.Entry(frame, width=30)
 self.usage_entry.grid(row=4, column=1, pady=5, padx=5, sticky="w")

 ttk.Label(frame, text="Description:").grid(row=5, column=0, pady=5, sticky="w")
 self.description_text = tk.Text(frame, width=30, height=3)
 self.description_text.grid(row=5, column=1, pady=5, padx=5, sticky="w")

 # Boutons
 button_frame = ttk.Frame(frame)
 button_frame.grid(row=6, column=0, columnspan=2, pady=10)

 ttk.Button(button_frame, text="Ajouter", command=self.add_appliance).pack(side="left", padx=5)
 ttk.Button(button_frame, text="Modifier", command=self.modify_appliance).pack(side="left", padx=5)
 ttk.Button(button_frame, text="Supprimer", command=self.delete_appliance).pack(side="left", padx=5)

 # Tableau des données
 ttk.Label(frame, text="Appareils Enregistrés", font=("Arial", 12, "bold")).grid(row=7, column=0, columnspan=2, pady=10, sticky="w")

 # Création du treeview (tableau)
 self.appliance_tree = ttk.Treeview(frame, columns=("name", "category", "power", "usage", "monthly"), show="headings", height=10)
 self.appliance_tree.grid(row=8, column=0, columnspan=2, sticky="nsew")

 # Configuration des colonnes
 self.appliance_tree.heading("name", text="Appareil")
 self.appliance_tree.heading("category", text="Catégorie")
 self.appliance_tree.heading("power", text="Puissance (W)")
 self.appliance_tree.heading("usage", text="Utilisation (h/jour)")
 self.appliance_tree.heading("monthly", text="Conso. Mensuelle (kWh)")

 self.appliance_tree.column("name", width=150)
 self.appliance_tree.column("category", width=100)
 self.appliance_tree.column("power", width=100)
 self.appliance_tree.column("usage", width=120)
 self.appliance_tree.column("monthly", width=150)

 # Scrollbar
 scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.appliance_tree.yview)
 scrollbar.grid(row=8, column=2, sticky="ns")
 self.appliance_tree.configure(yscrollcommand=scrollbar.set)

 # Gestion de l'événement de sélection
 self.appliance_tree.bind("<<TreeviewSelect>>", self.on_appliance_select)

 # Chargement des données
 self.load_appliance_data()

 # Configurer le redimensionnement
 frame.columnconfigure(1, weight=1)
 frame.rowconfigure(8, weight=1)

 def load_appliance_data(self):
 """Charge les données des appareils depuis la base de données"""
 # Effacer le tableau
 for item in self.appliance_tree.get_children():
 self.appliance_tree.delete(item)

 # Charger les données
 query = "SELECT id, name, category, power, usage_hours FROM appliances ORDER BY category, name"
 data = self.execute_query(query, fetch=True)

 if data:
 for row in data:
 id, name, category, power, usage = row
 # Calculer la consommation mensuelle (kWh)
 monthly_consumption = (power * usage * 30) / 1000

 # Stocker l'ID en tant que tags pour pouvoir le récupérer plus tard
 self.appliance_tree.insert("", "end", values=(name, category, power, usage, f"{monthly_consumption:.2f}"), tags=(id,))

 def add_appliance(self):
 """Ajoute un nouvel appareil dans la base de données"""
 name = self.appliance_name_entry.get().strip()
 category = self.category_var.get()
 power_str = self.power_entry.get().strip()
 usage_str = self.usage_entry.get().strip()
 description = self.description_text.get("1.0", tk.END).strip()

 if not name or not power_str or not usage_str:
 messagebox.showwarning("Champs Manquants", "Veuillez remplir tous les champs obligatoires.")
 return

 try:
 power = float(power_str)
 usage = float(usage_str)
 except ValueError:
 messagebox.showwarning("Erreur de Format", "La puissance et l'utilisation doivent être des nombres.")
 return

 # Ajouter le nouvel appareil
 query = "INSERT INTO appliances (name, category, power, usage_hours, description) VALUES (%s, %s, %s, %s, %s)"
 self.execute_query(query, (name, category, power, usage, description))
 messagebox.showinfo("Succès", "Appareil ajouté avec succès.")

 # Effacer les champs
 self.appliance_name_entry.delete(0, tk.END)
 self.category_combobox.current(0)
 self.power_entry.delete(0, tk.END)
 self.usage_entry.delete(0, tk.END)
 self.description_text.delete("1.0", tk.END)

 # Recharger les données
 self.load_appliance_data()

 def modify_appliance(self):
 """Modifie un appareil existant"""
 selection = self.appliance_tree.selection()
 if not selection:
 messagebox.showwarning("Sélection Requise", "Veuillez sélectionner un appareil à modifier.")
 return

 name = self.appliance_name_entry.get().strip()
 category = self.category_var.get()
 power_str = self.power_entry.get().strip()
 usage_str = self.usage_entry.get().strip()
 description = self.description_text.get("1.0", tk.END).strip()

 if not name or not power_str or not usage_str:
 messagebox.showwarning("Champs Manquants", "Veuillez remplir tous les champs obligatoires.")
 return

 try:
 power = float(power_str)
 usage = float(usage_str)
 except ValueError:
 messagebox.showwarning("Erreur de Format", "La puissance et l'utilisation doivent être des nombres.")
 return

 # Récupérer l'ID de l'appareil (stocké en tant que tags)
 appliance_id = self.appliance_tree.item(selection[0], "tags")[0]

 # Mettre à jour la base de données
 query = "UPDATE appliances SET name = %s, category = %s, power = %s, usage_hours = %s, description = %s WHERE id = %s"
 self.execute_query(query, (name, category, power, usage, description, appliance_id))
 messagebox.showinfo("Succès", "Appareil mis à jour avec succès.")

 # Effacer les champs
 self.appliance_name_entry.delete(0, tk.END)
 self.category_combobox.current(0)
 self.power_entry.delete(0, tk.END)
 self.usage_entry.delete(0, tk.END)
 self.description_text.delete("1.0", tk.END)

 # Recharger les données
 self.load_appliance_data()

 def delete_appliance(self):
 """Supprime un appareil existant"""
 selection = self.appliance_tree.selection()
 if not selection:
 messagebox.showwarning("Sélection Requise", "Veuillez sélectionner un appareil à supprimer.")
 return

 # Confirmation
 confirm = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cet appareil? Tous les services associés seront également supprimés.")
 if not confirm:
 return

 # Récupérer l'ID de l'appareil (stocké en tant que tags)
 appliance_id = self.appliance_tree.item(selection[0], "tags")[0]

 # Supprimer de la base de données (les services associés seront également supprimés grâce à ON DELETE CASCADE)
 query = "DELETE FROM appliances WHERE id = %s"
 self.execute_query(query, (appliance_id,))
 messagebox.showinfo("Succès", "Appareil supprimé avec succès.")

 # Effacer les champs
 self.appliance_name_entry.delete(0, tk.END)
 self.category_combobox.current(0)
 self.power_entry.delete(0, tk.END)
 self.usage_entry.delete(0, tk.END)
 self.description_text.delete("1.0", tk.END)

 # Recharger les données
 self.load_appliance_data()

 def on_appliance_select(self, event):
 """Remplit les champs lorsqu'un élément est sélectionné dans le tableau"""
 selection = self.appliance_tree.selection()
 if selection:
 item = self.appliance_tree.item(selection[0])
 name, category, power, usage, _ = item["values"]
 appliance_id = item["tags"][0]

 # Récupérer la description
 query = "SELECT description FROM appliances WHERE id = %s"
 result = self.execute_query(query, (appliance_id,), fetch=True)
 description = result[0][0] if result and result[0][0] else ""

 # Mettre à jour les champs
 self.appliance_name_entry.delete(0, tk.END)
 self.appliance_name_entry.insert(0, name)

 if category in self.appliance_categories:
 self.category_combobox.set(category)

 self.power_entry.delete(0, tk.END)
 self.power_entry.insert(0, str(power))

 self.usage_entry.delete(0, tk.END)
 self.usage_entry.insert(0, str(usage))

 self.description_text.delete("1.0", tk.END)
 self.description_text.insert("1.0", description)

 # Onglet Services
 def setup_services_tab(self):
 frame = ttk.Frame(self.tab_services, padding=20)
 frame.pack(fill="both", expand=True)

 # Division de l'écran en deux parties
 left_frame = ttk.Frame(frame)
 left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

 right_frame = ttk.Frame(frame)
 right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

 # Partie gauche : Liste des appareils
 ttk.Label(left_frame, text="Appareils Disponibles", font=("Arial", 12, "bold")).pack(pady=10, anchor="w")

 # Treeview pour les appareils
 self.services_appliance_tree = ttk.Treeview(left_frame, columns=("name", "category"), show="headings", height=15)
 self.services_appliance_tree.pack(fill="both", expand=True)

 # Configuration des colonnes
 self.services_appliance_tree.heading("name", text="Appareil")
 self.services_appliance_tree.heading("category", text="Catégorie")
 self.services_appliance_tree.column("name", width=150)
 self.services_appliance_tree.column("category", width=100)

 # Scrollbar
 scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.services_appliance_tree.yview)
 scrollbar.pack(side="right", fill="y")
 self.services_appliance_tree.configure(yscrollcommand=scrollbar.set)

 # Sélection d'un appareil pour voir/ajouter des services
 self.services_appliance_tree.bind("<<TreeviewSelect>>", self.on_services_appliance_select)

 # Partie droite : Services de l'appareil sélectionné
 self.services_detail_frame = ttk.LabelFrame(right_frame, text="Services de l'appareil", padding=10)
 self.services_detail_frame.pack(fill="both", expand=True)

 # Formulaire pour ajouter un service
 service_form_frame = ttk.Frame(self.services_detail_frame)
 service_form_frame.pack(fill="x", pady=10)

 ttk.Label(service_form_frame, text="Nom du service:").grid(row=0, column=0, sticky="w", pady=5)
 self.service_name_entry = ttk.Entry(service_form_frame, width=30)
 self.service_name_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

 ttk.Label(service_form_frame, text="Surcoût énergétique (W):").grid(row=1, column=0, sticky="w", pady=5)
 self.service_power_entry = ttk.Entry(service_form_frame, width=30)
 self.service_power_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

 ttk.Label(service_form_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
 self.service_description_text = tk.Text(service_form_frame, width=30, height=3)
 self.service_description_text.grid(row=2, column=1, sticky="w", padx=5, pady=5)

 # Boutons pour la gestion des services
 service_button_frame = ttk.Frame(self.services_detail_frame)
 service_button_frame.pack(fill="x", pady=10)

 self.service_add_button = ttk.Button(service_button_frame, text="Ajouter Service", command=self.add_service, state="disabled")
 self.service_add_button.pack(side="left", padx=5)

 self.service_modify_button = ttk.Button(service_button_frame, text="Modifier Service", command=self.modify_service, state="disabled")
 self.service_modify_button.pack(side="left", padx=5)

 self.service_delete_button = ttk.Button(service_button_frame, text="Supprimer Service", command=self.delete_service, state="disabled")
 self.service_delete_button.pack(side="left", padx=5)

 # Tableau des services
 ttk.Label(self.services_detail_frame, text="Services configurés", font=("Arial", 11)).pack(anchor="w", pady=5)

 self.services_tree = ttk.Treeview(self.services_detail_frame, columns=("name", "power", "impact"), show="headings", height=8)
 self.services_tree.pack(fill="both", expand=True)

 # Configuration des colonnes
 self.services_tree.heading("name", text="Service")
 self.services_tree.heading("power", text="Surcoût (W)")
 self.services_tree.heading("impact", text="Impact (kWh/mois)")

 self.services_tree.column("name", width=150)
 self.services_tree.column("power", width=100)
 self.services_tree.column("impact", width=120)

 # Scrollbar
 scrollbar_services = ttk.Scrollbar(self.services_detail_frame, orient="vertical", command=self