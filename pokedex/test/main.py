import pip
import sys
import os
from datetime import datetime

try:
    # Tentar importar os módulos necessários
    import customtkinter as ctk
    import requests
    from tkinter import Tk, PhotoImage, messagebox
    from PIL import ImageTk, Image
    from urllib.request import urlopen
    import pickle
    import webbrowser
    import json
    print("Todos os módulos encontrados")
except ModuleNotFoundError as e:
    # Se algum módulo não for encontrado, instalar automaticamente
    print(f"Módulo não encontrado: {e}. Tentando instalar...")
    pip.main(["install", "customtkinter", "requests", "pillow"])
    # Reiniciar o script após a instalação
    os.execv(sys.executable, ['python'] + sys.argv)

# Constantes do aplicativo
APP_VERSION = "2.0"
DATA_FILE = "pk_db.pickle"  # Arquivo para armazenar os dados dos pokémons
CONFIG_FILE = "pokedex_config.json"  # Arquivo de configurações
ICON_FILE = "icon_pk.ico"  # Ícone do aplicativo
TITLE_IMAGE = "title.png"  # Imagem do título
PK_BALL_IMAGE = "pk_ball.png"  # Imagem da pokébola

class PokedexApp:
    def __init__(self):
        """Inicializa a aplicação Pokedex"""
        self.main_w = ctk.CTk()  # Janela principal
        self.pk_db = None  # Dados dos pokémons
        self.current_pokemon = 1  # Pokémon atualmente exibido
        self.favorites = set()  # Conjunto de favoritos
        self.theme = "dark"  # Tema padrão
        self.color_theme = "dark-blue"  # Tema de cores padrão
        self.load_config()  # Carrega as configurações
        self.setup_window()  # Configura a janela
        self.load_data()  # Carrega os dados dos pokémons
        self.setup_main_screen()  # Configura a tela principal
        self.main_w.mainloop()  # Inicia o loop principal

    def load_config(self):
        """Carrega as configurações do arquivo ou define padrões"""
        # Configurações padrão
        defaults = {
            "window_size": [800, 800],
            "theme": "dark",
            "color_theme": "dark-blue",
            "favorites": []
        }
        
        try:
            # Tenta carregar o arquivo de configuração
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.window_size = config.get("window_size", defaults["window_size"])
                self.theme = config.get("theme", defaults["theme"])
                self.color_theme = config.get("color_theme", defaults["color_theme"])
                self.favorites = set(config.get("favorites", defaults["favorites"]))
        except (FileNotFoundError, json.JSONDecodeError):
            # Se houver erro, usa as configurações padrão
            self.window_size = defaults["window_size"]
            self.theme = defaults["theme"]
            self.color_theme = defaults["color_theme"]
            self.favorites = set(defaults["favorites"])

    def save_config(self):
        """Salva a configuração atual no arquivo"""
        config = {
            "window_size": self.window_size,
            "theme": self.theme,
            "color_theme": self.color_theme,
            "favorites": list(self.favorites)
        }
        
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")

    def setup_window(self):
        """Configura as definições da janela principal"""
        self.main_w.title(f"Pokedex App v{APP_VERSION}")
        self.main_w.geometry(f"{self.window_size[0]}x{self.window_size[1]}")
        self.main_w.resizable(True, True)  # Permite redimensionamento
        
        try:
            self.main_w.iconbitmap(ICON_FILE)  # Define o ícone
        except:
            print("Arquivo de ícone não encontrado")
        
        # Define o tema visual
        ctk.set_appearance_mode(self.theme)
        ctk.set_default_color_theme(self.color_theme)
        
        # Define tamanhos mínimo e máximo da janela
        self.main_w.minsize(600, 600)
        self.main_w.maxsize(1200, 900)

    def load_data(self):
        """Carrega os dados dos pokémons da API ou do cache"""
        try:
            # Tenta carregar do arquivo de cache
            with open(DATA_FILE, "rb") as file:
                self.pk_db = pickle.load(file)
                print("Dados dos pokémons carregados do cache")
        except Exception as e:
            print(f"Cache não encontrado ou erro ao carregar: {e}")
            self.fetch_pokemon_data()  # Se falhar, busca da API

    def fetch_pokemon_data(self):
        """Busca dados dos pokémons da PokeAPI"""
        print("Buscando dados da PokeAPI...")
        try:
            # Obtém a lista de pokémons
            api_response = requests.get("https://pokeapi.co/api/v2/pokedex/2/")
            api_response.raise_for_status()  # Verifica erros
            dex_data = api_response.json()
            
            # Cria dicionário de pokémons
            self.pk_db = {}
            for entry in dex_data["pokemon_entries"]:
                pokemon_id = entry["entry_number"]
                name = entry["pokemon_species"]["name"].title()
                self.pk_db[pokemon_id] = {"name": name}
            
            # Obtém detalhes adicionais para cada pokémon
            for pokemon_id in self.pk_db:
                # Dados da espécie (para taxa de captura)
                species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/"
                species_data = requests.get(species_url).json()
                self.pk_db[pokemon_id]["catch_rate"] = species_data.get("capture_rate", 0)
                
                # Dados do pokémon (para sprites e tipos)
                pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}/"
                pokemon_data = requests.get(pokemon_url).json()
                
                # Armazena URL do sprite
                self.pk_db[pokemon_id]["sprite"] = pokemon_data["sprites"]["other"]["official-artwork"]["front_default"]
                
                # Armazena tipos
                self.pk_db[pokemon_id]["types"] = [t["type"]["name"].title() for t in pokemon_data["types"]]
                
                # Armazena estatísticas
                self.pk_db[pokemon_id]["stats"] = {s["stat"]["name"].title(): s["base_stat"] for s in pokemon_data["stats"]}
                
                # Armazena altura e peso
                self.pk_db[pokemon_id]["height"] = pokemon_data["height"] / 10  # Converte para metros
                self.pk_db[pokemon_id]["weight"] = pokemon_data["weight"] / 10  # Converte para kg
                
                print(f"Dados obtidos para {self.pk_db[pokemon_id]['name']} (#{pokemon_id})")
                
                # Pequeno delay para não sobrecarregar a API
                import time
                time.sleep(0.1)
            
            # Salva os dados no arquivo
            with open(DATA_FILE, "wb") as file:
                pickle.dump(self.pk_db, file)
                
        except requests.RequestException as e:
            messagebox.showerror("Erro na API", f"Falha ao buscar dados da PokeAPI: {e}")
            sys.exit(1)

    def setup_main_screen(self):
        """Cria a tela inicial/principal"""
        self.main_frame = ctk.CTkFrame(master=self.main_w)
        self.main_frame.pack(fill="both", expand=True)
        
        # Imagem do título
        try:
            img = PhotoImage(file=TITLE_IMAGE)
            self.image_title = ctk.CTkLabel(master=self.main_frame, image=img, text="")
            self.image_title.place(relx=0.5, rely=0.2, anchor="center")
        except:
            self.image_title = ctk.CTkLabel(master=self.main_frame, text="POKEDEX", font=("Roboto", 48, "bold"))
            self.image_title.place(relx=0.5, rely=0.2, anchor="center")
        
        # Botão de iniciar
        self.start_button = ctk.CTkButton(
            master=self.main_frame,
            command=self.show_pokedex,
            text="INICIAR",
            fg_color="firebrick1",
            hover_color="firebrick3",
            font=("Roboto", 30, "bold"),
            corner_radius=40,
            width=200,
            height=100
        )
        self.start_button.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão de configurações
        self.settings_button = ctk.CTkButton(
            master=self.main_frame,
            command=self.show_settings,
            text="⚙️",
            font=("Arial", 20),
            width=40,
            height=40,
            corner_radius=20
        )
        self.settings_button.place(relx=0.95, rely=0.05, anchor="ne")
        
        # Créditos
        self.credit_info = ctk.CTkLabel(
            master=self.main_frame,
            text="Criado por: Gustavo Moreira\nGitHub: github.com/Gustav0Moreira\nVersão: " + APP_VERSION,
            font=("Roboto", 12)
        )
        self.credit_info.place(relx=0.5, rely=0.9, anchor="center")

    def show_settings(self):
        """Mostra o diálogo de configurações"""
        settings = ctk.CTkToplevel(self.main_w)
        settings.title("Configurações")
        settings.geometry("400x400")
        settings.resizable(False, False)
        settings.transient(self.main_w)  # Diálogo modal
        settings.grab_set()
        
        # Seleção de tema
        ctk.CTkLabel(settings, text="Modo de Aparência:", font=("Roboto", 14)).pack(pady=(20, 5))
        theme_var = ctk.StringVar(value=self.theme)
        theme_menu = ctk.CTkOptionMenu(
            settings,
            values=["dark", "light", "system"],
            variable=theme_var,
            command=self.change_theme
        )
        theme_menu.pack()
        
        # Seleção de tema de cores
        ctk.CTkLabel(settings, text="Tema de Cores:", font=("Roboto", 14)).pack(pady=(20, 5))
        color_var = ctk.StringVar(value=self.color_theme)
        color_menu = ctk.CTkOptionMenu(
            settings,
            values=["dark-blue", "green", "blue", "red"],
            variable=color_var,
            command=self.change_color_theme
        )
        color_menu.pack()
        
        # Botão para limpar cache
        ctk.CTkButton(
            settings,
            text="Limpar Cache",
            command=self.clear_cache,
            fg_color="red",
            hover_color="darkred"
        ).pack(pady=20)
        
        # Botão de fechar
        ctk.CTkButton(
            settings,
            text="Fechar",
            command=settings.destroy
        ).pack(pady=10)

    def change_theme(self, new_theme):
        """Altera o tema do aplicativo"""
        self.theme = new_theme
        ctk.set_appearance_mode(new_theme)
        self.save_config()

    def change_color_theme(self, new_color):
        """Altera o tema de cores"""
        self.color_theme = new_color
        ctk.set_default_color_theme(new_color)
        self.save_config()

    def clear_cache(self):
        """Limpa os dados em cache dos pokémons"""
        try:
            os.remove(DATA_FILE)
            messagebox.showinfo("Cache Limpo", "Os dados em cache foram apagados. Serão baixados novamente ao reiniciar o aplicativo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível limpar o cache: {e}")

    def show_pokedex(self):
        """Mostra a interface da pokédex"""
        self.main_frame.pack_forget()  # Remove a tela principal
        self.setup_pokedex_interface()  # Configura a interface da pokédex

    def setup_pokedex_interface(self):
        """Cria a interface de navegação da pokédex"""
        # Container principal
        self.pokedex_frame = ctk.CTkFrame(master=self.main_w)
        self.pokedex_frame.pack(fill="both", expand=True)
        
        # Painel esquerdo - Exibição do pokémon
        self.left_panel = ctk.CTkFrame(master=self.pokedex_frame, width=400)
        self.left_panel.pack(side="left", fill="both", expand=True)
        
        # Painel direito - Lista de pokémons
        self.right_panel = ctk.CTkScrollableFrame(master=self.pokedex_frame, width=400)
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        # Botão de voltar
        self.back_button = ctk.CTkButton(
            master=self.left_panel,
            command=self.return_to_main,
            text="← Voltar",
            font=("Roboto", 14),
            width=80,
            height=30,
            corner_radius=10,
            fg_color="gray30"
        )
        self.back_button.place(relx=0.05, rely=0.05, anchor="nw")
        
        # Campo de busca
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            master=self.left_panel,
            textvariable=self.search_var,
            placeholder_text="Buscar pokémon...",
            width=200
        )
        self.search_entry.place(relx=0.5, rely=0.05, anchor="n")
        self.search_entry.bind("<KeyRelease>", self.search_pokemon)
        
        # Navegação por ID
        self.nav_frame = ctk.CTkFrame(master=self.left_panel, height=40)
        self.nav_frame.place(relx=0.5, rely=0.12, anchor="n")
        
        self.prev_button = ctk.CTkButton(
            master=self.nav_frame,
            text="◄",
            command=lambda: self.show_pokemon(self.current_pokemon - 1),
            width=40,
            height=30
        )
        self.prev_button.pack(side="left", padx=5)
        
        self.id_entry = ctk.CTkEntry(
            master=self.nav_frame,
            width=60,
            justify="center"
        )
        self.id_entry.pack(side="left", padx=5)
        self.id_entry.bind("<Return>", lambda e: self.show_pokemon(int(self.id_entry.get())))
        
        self.next_button = ctk.CTkButton(
            master=self.nav_frame,
            text="►",
            command=lambda: self.show_pokemon(self.current_pokemon + 1),
            width=40,
            height=30
        )
        self.next_button.pack(side="left", padx=5)
        
        # Botão de favorito
        self.fav_button = ctk.CTkButton(
            master=self.nav_frame,
            text="★",
            command=self.toggle_favorite,
            width=40,
            height=30,
            fg_color="gold" if self.current_pokemon in self.favorites else "gray40"
        )
        self.fav_button.pack(side="left", padx=5)
        
        # Imagem do pokémon
        self.pokemon_image = ctk.CTkLabel(master=self.left_panel, text="")
        self.pokemon_image.place(relx=0.5, rely=0.25, anchor="n")
        
        # Frame de informações do pokémon
        self.info_frame = ctk.CTkFrame(master=self.left_panel)
        self.info_frame.place(relx=0.5, rely=0.6, anchor="n", relwidth=0.9)
        
        # Nome e ID do pokémon
        self.name_label = ctk.CTkLabel(
            master=self.info_frame,
            font=("Roboto", 24, "bold"),
            text=""
        )
        self.name_label.pack(pady=5)
        
        # Tipos
        self.type_frame = ctk.CTkFrame(master=self.info_frame, fg_color="transparent")
        self.type_frame.pack(pady=5)
        
        # Estatísticas
        self.stats_frame = ctk.CTkFrame(master=self.info_frame, fg_color="transparent")
        self.stats_frame.pack(pady=5)
        
        # Taxa de captura
        self.capture_label = ctk.CTkLabel(
            master=self.info_frame,
            font=("Roboto", 16),
            text=""
        )
        self.capture_label.pack(pady=5)
        
        # Altura e peso
        self.size_frame = ctk.CTkFrame(master=self.info_frame, fg_color="transparent")
        self.size_frame.pack(pady=5)
        
        # Cria os botões da lista de pokémons
        self.create_pokemon_list()
        
        # Mostra o primeiro pokémon
        self.show_pokemon(1)

    def create_pokemon_list(self):
        """Cria botões para todos os pokémons na lista"""
        for pokemon_id in sorted(self.pk_db.keys()):
            name = self.pk_db[pokemon_id]["name"].lower()
            
            btn = ctk.CTkButton(
                master=self.right_panel,
                text=f"{self.pk_db[pokemon_id]['name']} #{pokemon_id}",
                command=lambda id=pokemon_id: self.show_pokemon(id),
                font=("Roboto", 14),
                fg_color="firebrick3",
                hover_color="firebrick4",
                width=350,
                height=40,
                corner_radius=10
            )
            
            # Destaque para favoritos
            if pokemon_id in self.favorites:
                btn.configure(fg_color="gold", text_color="black", hover_color="goldenrod")
            
            btn.pack(pady=5)

    def show_pokemon(self, pokemon_id):
        """Exibe informações de um pokémon específico"""
        # Valida o ID
        if pokemon_id < 1:
            pokemon_id = 1
        elif pokemon_id > len(self.pk_db):
            pokemon_id = len(self.pk_db)
        
        self.current_pokemon = pokemon_id
        pokemon = self.pk_db[pokemon_id]
        
        # Atualiza a navegação
        self.id_entry.delete(0, "end")
        self.id_entry.insert(0, str(pokemon_id))
        self.fav_button.configure(fg_color="gold" if pokemon_id in self.favorites else "gray40")
        
        #imagens
        try:
            img = Image.open(urlopen(pokemon["sprite"]))
            img = img.resize((250, 250), Image.LANCZOS)  #Redimensionar com anti-aliasing
            img = ImageTk.PhotoImage(img)
            self.pokemon_image.configure(image=img)
            self.pokemon_image.image = img  #referência
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")
            self.pokemon_image.configure(text="Imagem não disponível")
        
        # Atualiza nome e ID
        self.name_label.configure(text=f"{pokemon['name']} #{pokemon_id}")
        
        # Atualiza os tipos
        for widget in self.type_frame.winfo_children():
            widget.destroy()
            
        for type_name in pokemon["types"]:
            color = self.get_type_color(type_name.lower())
            ctk.CTkLabel(
                master=self.type_frame,
                text=type_name,
                font=("Roboto", 14, "bold"),
                fg_color=color,
                corner_radius=10,
                padx=10,
                pady=5
            ).pack(side="left", padx=5)
        
        """### Atualiza as estatísticas
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
            
        for stat, value in pokemon["stats"].items():
            frame = ctk.CTkFrame(master=self.stats_frame, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                master=frame,
                text=stat,
                width=100,
                anchor="w"
            ).pack(side="left")
            
            # Barra de progresso para as estatísticas
            progress_bar = ctk.CTkProgressBar(
                master=frame,
                width=150,
                height=15,
                orientation="horizontal"
            )
            progress_bar.pack(side="left", padx=5)
            
            # Define o valor da barra (escalonado para 0-1)
            max_stat = 255  # Valor máximo de estatística em pokémon
            progress = value / max_stat
            progress_bar.set(progress)
            
            ctk.CTkLabel(
                master=frame,
                text=str(value),
                width=30
            ).pack(side="left")
        
        # atualiza a taxa de captura
        catch_rate = pokemon["catch_rate"]
        if catch_rate <= 5:
            cr_text = "Impossível"
            color = "purple"
        elif catch_rate <= 45:
            cr_text = "Difícil"
            color = "red"
        elif catch_rate <= 150:
            cr_text = "Médio"
            color = "orange"
        else:
            cr_text = "Fácil"
            color = "green"
        
        self.capture_label.configure(
            text=f"Taxa de Captura: {cr_text} ({catch_rate})",
            fg_color=color
        )
        
        # atualiza altura e peso
        for widget in self.size_frame.winfo_children():
            widget.destroy()
            
        ctk.CTkLabel(
            master=self.size_frame,
            text=f"Altura: {pokemon['height']} m",
            font=("Roboto", 14)
        ).pack(side="left", padx=10)
        
        ctk.CTkLabel(
            master=self.size_frame,
            text=f"Peso: {pokemon['weight']} kg",
            font=("Roboto", 14)
        ).pack(side="left", padx=10)"""

    def get_type_color(self, type_name):
        """retorna a cor associada ao tipo de pokémon"""
        type_colors = {
            "normal": "#A8A878",
            "fire": "#F08030",
            "water": "#6890F0",
            "electric": "#F8D030",
            "grass": "#78C850",
            "ice": "#98D8D8",
            "fighting": "#C03028",
            "poison": "#A040A0",
            "ground": "#E0C068",
            "flying": "#A890F0",
            "psychic": "#F85888",
            "bug": "#A8B820",
            "rock": "#B8A038",
            "ghost": "#705898",
            "dragon": "#7038F8",
            "dark": "#705848",
            "steel": "#B8B8D0",
            "fairy": "#EE99AC"
        }
        return type_colors.get(type_name, "#777777")  # Cor padrão se não for encontrado

    def toggle_favorite(self):
        """Alterna o pokémon atual como favorito"""
        if self.current_pokemon in self.favorites:
            self.favorites.remove(self.current_pokemon)
            self.fav_button.configure(fg_color="gray40")
        else:
            self.favorites.add(self.current_pokemon)
            self.fav_button.configure(fg_color="gold")
        
        # atualiza a lista dos pokémons 
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        self.create_pokemon_list()
        
        self.save_config()  # Salvamento

    def search_pokemon(self, event=None):
        """Filtra a lista de pokémons baseados da busca"""
        search_term = self.search_var.get().lower()
        
        # limpa lista
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        # recria a lista apenas com os pokémons da busca
        for pokemon_id in sorted(self.pk_db.keys()):
            name = self.pk_db[pokemon_id]["name"].lower()
            if search_term in name or search_term in str(pokemon_id):
                btn = ctk.CTkButton(
                    master=self.right_panel,
                    text=f"{self.pk_db[pokemon_id]['name']} #{pokemon_id}",
                    command=lambda id=pokemon_id: self.show_pokemon(id),
                    font=("Roboto", 14),
                    fg_color="firebrick3",
                    hover_color="firebrick4",
                    width=350,
                    height=40,
                    corner_radius=10
                )
                
                if pokemon_id in self.favorites:
                    btn.configure(fg_color="gold", text_color="black", hover_color="goldenrod")
                
                btn.pack(pady=5)

    def return_to_main(self):
        """Volta para a tela principal"""
        self.pokedex_frame.pack_forget()
        self.setup_main_screen()

if __name__ == "__main__":
    PokedexApp()  