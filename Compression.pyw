import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ExifTags
import os
import zipfile
from datetime import datetime
import threading
from pillow_heif import register_heif_opener

# Enregistrer le plugin HEIF pour Pillow pour permettre l'ouverture des fichiers HEIC
register_heif_opener()

def open_image(file_path):
    """Ouvre une image en utilisant PIL, supporte aussi les fichiers HEIC."""
    try:
        return Image.open(file_path)
    except IOError as e:
        return f"Erreur lors de l'ouverture du fichier {file_path}: {e}"

def format_size(size):
    """Formate la taille du fichier en ko ou Mo avec des virgules comme séparateurs de milliers."""
    size_kb = size / 1024
    if size_kb < 1024:
        return f"{size_kb:,.0f} ko".replace(",", " ")
    else:
        size_mb = size_kb / 1024
        return f"{size_mb:,.2f} Mo".replace(",", " ")

def select_folder(tree):
    """Permet à l'utilisateur de sélectionner un dossier et liste les fichiers image avec leur taille dans le treeview."""
    folder_path = filedialog.askdirectory()
    if folder_path:
        tree.delete(*tree.get_children())
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    file_size_str = format_size(file_size)
                    tree.insert('', 'end', values=(file_path, file_size_str))

def select_files(tree):
    """Permet à l'utilisateur de sélectionner des fichiers image et les ajoute au treeview avec leur taille."""
    file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg *.jpeg *.png *.heic")])
    if file_paths:
        for path in file_paths:
            file_size = os.path.getsize(path)
            file_size_str = format_size(file_size)
            tree.insert('', 'end', values=(path, file_size_str))

def delete_selected_files(tree):
    """Supprime les fichiers sélectionnés dans le treeview."""
    selected_items = tree.selection()
    for item in selected_items:
        tree.delete(item)

def clear_tree(tree):
    """Vide tous les éléments du treeview."""
    tree.delete(*tree.get_children())

def apply_exif_orientation(image):
    """Applique l'orientation EXIF à une image PIL."""
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            exif = dict(exif.items())
            orientation = exif.get(orientation)
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image

def compress_and_save(tree, progress_bar, progress_label, delete_originals):
    def compress_task():
        selected_items = tree.get_children()
        if not selected_items:
            messagebox.showwarning("Attention", "Aucun fichier ou dossier sélectionné. Veuillez sélectionner un fichier ou un dossier.")
            return

        current_date = datetime.now().strftime("%Y_%m_%d")
        files_to_zip = {}

        for item in selected_items:
            file_path = tree.item(item, 'values')[0]
            directory = os.path.dirname(file_path)
            if directory not in files_to_zip:
                files_to_zip[directory] = []
            files_to_zip[directory].append(file_path)

        total_files = sum(len(files) for files in files_to_zip.values())
        progress_bar['maximum'] = total_files
        progress_bar['value'] = 0
        progress_label.config(text=f"Progression: 0/{total_files} fichiers")

        processed_files = 0

        for directory, files in files_to_zip.items():
            zip_filepath = os.path.join(directory, f"original_{current_date}.zip")

            if not delete_originals.get():
                with zipfile.ZipFile(zip_filepath, 'a', zipfile.ZIP_DEFLATED) as original_zipf:
                    for file_path in files:
                        try:
                            image = open_image(file_path)
                            if image:
                                image = apply_exif_orientation(image)
                                original_name = os.path.basename(file_path).rsplit('.', 1)[0]
                                new_name = f"{original_name}_comp_{current_date}.jpg"
                                compressed_path = os.path.join(directory, new_name)

                                if image.mode != "RGB":
                                    image = image.convert("RGB")

                                quality = 95
                                while True:
                                    image.save(compressed_path, "JPEG", quality=quality)
                                    if os.path.getsize(compressed_path) <= 500 * 1024 or quality <= 5:
                                        break
                                    quality -= 5

                                image.close()

                                original_zipf.write(file_path, os.path.basename(file_path))
                                os.remove(file_path)  # Remove the original file after adding to zip

                            progress_bar['value'] += 1
                            processed_files += 1
                            progress_label.config(text=f"Progression: {processed_files}/{total_files} fichiers")
                            root.update_idletasks()
                        except Exception as e:
                            messagebox.showerror("Erreur", f"Erreur lors de la compression de l'image: {e}")
                            continue
            else:
                for file_path in files:
                    try:
                        image = open_image(file_path)
                        if image:
                            image = apply_exif_orientation(image)
                            original_name = os.path.basename(file_path).rsplit('.', 1)[0]
                            new_name = f"{original_name}_comp_{current_date}.jpg"
                            compressed_path = os.path.join(directory, new_name)

                            if image.mode != "RGB":
                                image = image.convert("RGB")

                            quality = 95
                            while True:
                                image.save(compressed_path, "JPEG", quality=quality)
                                if os.path.getsize(compressed_path) <= 500 * 1024 or quality <= 5:
                                    break
                                quality -= 5

                            image.close()
                            os.remove(file_path)  # Remove the original file after compression

                            progress_bar['value'] += 1
                            processed_files += 1
                            progress_label.config(text=f"Progression: {processed_files}/{total_files} fichiers")
                            root.update_idletasks()
                    except Exception as e:
                        messagebox.showerror("Erreur", f"Erreur lors de la compression de l'image: {e}")
                        continue

        progress_bar['value'] = total_files
        progress_label.config(text=f"Progression: {total_files}/{total_files} fichiers")
        
        if delete_originals.get():
            messagebox.showinfo("Succès", "La compression des fichiers sélectionnés est terminée.")
        else:
            messagebox.showinfo("Succès", "La compression des fichiers sélectionnés est terminée. Vous retrouverez vos fichiers originaux dans un fichier zip dans le répertoire.")
        
        progress_bar['value'] = 0
        progress_label.config(text="Progression: 0/0 fichiers")
        clear_tree(tree)
        
        # Reset the checkbox
        delete_originals.set(False)

    threading.Thread(target=compress_task).start()

def main():

    base_path = os.path.dirname(os.path.abspath(__file__))
    
    image_path = os.path.join(base_path, 'Assets', 'parislo.png')

    # Vérifiez si le fichier existe
    if not os.path.exists(image_path):
        return f"Le fichier {image_path} n'existe pas."
    
    global root
    root = tk.Tk()
    root.title("Compression d'Images")
    root.geometry("875x700")
    root.minsize(875, 700)
    root.configure(bg="#D6E8FE")
    root.resizable(False, False)

    icon_path = os.path.join(base_path, 'Assets', 'icon.ico')
    root.iconbitmap(icon_path)

    # Charger et redimensionner l'image
    image = Image.open(image_path)
    image = image.resize((100, 100), Image.LANCZOS)  # Redimensionner l'image
    photo = ImageTk.PhotoImage(image)

    # Créer un widget Label pour afficher l'image
    label_image = tk.Label(root, image=photo, bg="#D6E8FE")
    label_image.grid(row=0, column=0, padx=15, pady=5, sticky="nw")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Arial", 12), padding=10, background="#0052cc", foreground="white")
    style.map("TButton", background=[("active", "#004bb5"), ("pressed", "#003d99")])

    title_label = tk.Label(root, text="Compression d'Images", font=("Arial", 24), bg="#D6E8FE")
    title_label.grid(row=0, column=0, columnspan=5, padx=5, pady=10)

    button_frame = tk.Frame(root, bg="#D6E8FE")
    button_frame.grid(row=1, column=0, columnspan=5, pady=10, sticky="ew")

    select_folder_button = ttk.Button(button_frame, text="Sélectionner un Dossier", command=lambda: select_folder(tree))
    select_folder_button.pack(side="left", padx=10, pady=5, fill="x", expand=True)

    select_files_button = ttk.Button(button_frame, text="Sélectionner des Fichiers", command=lambda: select_files(tree))
    select_files_button.pack(side="left", padx=10, pady=5, fill="x", expand=True)

    delete_files_button = ttk.Button(button_frame, text="Supprimer Fichiers Sélectionnés", command=lambda: delete_selected_files(tree))
    delete_files_button.pack(side="left", padx=10, pady=5, fill="x", expand=True)

    clear_list_button = ttk.Button(button_frame, text="Vider Liste", command=lambda: clear_tree(tree))
    clear_list_button.pack(side="left", padx=10, pady=5, fill="x", expand=True)

    cols = ('Chemin du fichier', 'Taille')
    tree = ttk.Treeview(root, columns=cols, show='headings', height=15)
    for col in cols:
        tree.heading(col, text=col)
    tree.column('Chemin du fichier', anchor='nw', width=600)
    tree.column('Taille', anchor='ne', width=100)
    tree.grid(row=2, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

    delete_originals = tk.BooleanVar()
    
    delete_originals_check = tk.Checkbutton(root, text="Supprimer les fichiers originaux", variable=delete_originals, bg="#D6E8FE")
    delete_originals_check.grid(row=3, column=0, columnspan=5, pady=10)

    compress_button = ttk.Button(root, text="Compresser", command=lambda: compress_and_save(tree, progress_bar, progress_label, delete_originals), style="TButton")
    compress_button.grid(row=4, column=0, columnspan=5, pady=10)

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress_bar.grid(row=5, column=0, columnspan=5, pady=20)

    progress_label = tk.Label(root, text="Progression: 0/0 fichiers", bg="#D6E8FE")
    progress_label.grid(row=6, column=0, columnspan=5, pady=5)

    footer_frame = tk.Frame(root, bg="#D6E8FE")
    footer_frame.grid(row=7, column=0, columnspan=5, pady=10, sticky="ew")

    footer_left = tk.Label(footer_frame, text="DLH P2EN", bg="#D6E8FE", fg="black")
    footer_left.pack(side="left", padx=15)

    footer_right = tk.Label(footer_frame, text="Créé par MUSQUET Andy", bg="#D6E8FE", fg="black")
    footer_right.pack(side="right", padx=10)

    for i in range(8):
        root.grid_rowconfigure(i, weight=1)
    for i in range(5):
        root.grid_columnconfigure(i, weight=1)

    root.mainloop()

if __name__ == "__main__":
    main()
