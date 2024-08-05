import os
import tkinter as tk
from tkinter import filedialog, Text, Listbox, StringVar, Frame, Button
import UnityPy  # Import UnityPy module

class DraggableButtonList(Frame):
    def __init__(self, master, items, **kwargs):
        super().__init__(master, **kwargs)
        self.items = items
        self.buttons = []
        self.selected_button = None
        self.init_buttons()
        
    def init_buttons(self):
        for idx, item in enumerate(self.items):
            self.add_button(item, idx)
        self.update_button_texts()
    
    def add_button(self, item, index):
        button = Button(self, text=item, relief="raised", bg="#444", fg="white", highlightbackground="#333")
        button.grid(row=index, column=0, sticky="ew", pady=2)
        button.bind('<Button-1>', self.on_button_press)
        button.bind('<B1-Motion>', self.on_button_drag)
        self.buttons.append(button)
    
    def on_button_press(self, event):
        self.selected_button = event.widget
    
    def on_button_drag(self, event):
        y = event.y_root - self.winfo_rooty()
        index = y // self.selected_button.winfo_height()
        index = max(0, min(index, len(self.buttons) - 1))
        
        if self.selected_button in self.buttons:
            current_index = self.buttons.index(self.selected_button)
            if current_index != index:
                self.buttons.pop(current_index)
                self.buttons.insert(index, self.selected_button)
                self.refresh_buttons()
                self.update_button_texts()
    
    def refresh_buttons(self):
        for idx, button in enumerate(self.buttons):
            button.grid(row=idx, column=0, sticky="ew", pady=2)
    
    def update_button_texts(self):
        for idx, button in enumerate(self.buttons):
            button_text = button.cget("text")
            if '. ' in button_text:
                button_text = button_text.split('. ', 1)[1]
            button.config(text=f"{idx + 1}. {button_text}")

# Function to list SkinnedMeshRenderers
def list_skinned_mesh_renderers(asset_path):
    env = UnityPy.load(asset_path)
    smr_details = []

    for obj in env.objects:
        if obj.type.name == "SkinnedMeshRenderer":
            data = obj.read()

            go_path_id = data.m_GameObject.path_id if hasattr(data.m_GameObject, 'path_id') else None
            go_name = None

            if go_path_id:
                for go_obj in env.objects:
                    if go_obj.path_id == go_path_id:
                        go_data = go_obj.read()
                        go_name = go_data.name
                        break

            if go_name:
                smr_details.append((obj.path_id, go_name, data.m_Bones, data.m_RootBone, data.m_Materials, data.m_Mesh))

    return smr_details

def get_smr_details(env, smr_detail):
    smr_path_id, go_name, bones, root_bone, materials, mesh = smr_detail
    root_bone_name = get_bone_name(env, root_bone.path_id)

    bone_details = [(idx, get_bone_name(env, bone.path_id), bone.path_id) for idx, bone in enumerate(bones)]
    material_details = [(idx, material.path_id, material.file_id) for idx, material in enumerate(materials)]
    mesh_details = (mesh.path_id, mesh.file_id)

    return {
        "smr_path_id": smr_path_id,
        "go_name": go_name,
        "root_bone_name": root_bone_name,
        "bone_details": bone_details,
        "material_details": material_details,
        "mesh_details": mesh_details
    }

def get_bone_name(env, bone_path_id):
    bone_obj = None
    bone_name = None

    for obj in env.objects:
        if obj.path_id == bone_path_id:
            bone_obj = obj.read()
            break

    if bone_obj:
        for obj in env.objects:
            if obj.type.name == "GameObject":
                go_data = obj.read()
                if any(comp.path_id == bone_path_id for comp in go_data.m_Components):
                    bone_name = go_data.name
                    break

    return bone_name or "Unknown"

# Function to truncate file paths
def truncate_path(path, max_length=40):
    if len(path) > max_length:
        return '...' + path[-max_length:]
    return path

# tkinter GUI integration
class PlayerBundleCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PlayerBundleCompare")

        # Set default window size (25% larger than before)
        self.root.geometry('1500x1000')  # Increased width by 25%

        # Set dark mode colors
        self.root.configure(bg="#333")
        frame = tk.Frame(self.root, bg="#333")
        frame.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")

        self.file1_button = tk.Button(frame, text="Load File 1", command=self.load_file1, bg="#555", fg="white", highlightbackground="#333")
        self.file1_button.grid(row=0, column=0, padx=5, pady=5)

        self.file1_label = tk.Label(frame, text="No file loaded", width=50, anchor="w", bg="#333", fg="white")
        self.file1_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.file2_button = tk.Button(frame, text="Load File 2", command=self.load_file2, bg="#555", fg="white", highlightbackground="#333")
        self.file2_button.grid(row=1, column=0, padx=5, pady=5)

        self.file2_label = tk.Label(frame, text="No file loaded", width=50, anchor="w", bg="#333", fg="white")
        self.file2_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.compare_button = tk.Button(frame, text="Load Data", command=self.load_data, state=tk.DISABLED, bg="#777", fg="white", highlightbackground="#333")
        self.compare_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Dropdown for selecting info type
        self.info_type_var = StringVar(self.root)
        self.info_type_var.set("Bones")
        self.info_type_menu = tk.OptionMenu(frame, self.info_type_var, "Bones", "Materials and Mesh", command=self.update_smr_list)
        self.info_type_menu.config(bg="#555", fg="white", highlightbackground="#555")
        self.info_type_menu["menu"].config(bg="#555", fg="white", activebackground="#777", activeforeground="white")
        self.info_type_menu.grid(row=3, column=0, columnspan=2, pady=5)

        # Listbox for SkinnedMeshRenderers
        self.smr_listbox = Listbox(self.root, width=80, bg="#444", fg="white", highlightbackground="#333", selectbackground="#555", selectforeground="white")  # Equal width for both listbox and text widget
        self.smr_listbox.grid(row=1, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.smr_listbox.bind("<<ListboxSelect>>", self.update_result_text)

        # Text widget for displaying result
        self.result_text = Text(self.root, height=20, width=80, bg="#444", fg="white", highlightbackground="#333")
        self.result_text.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Frame and draggable button list for reordering items
        self.drag_frame = Frame(self.root, bg="#333")
        self.drag_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        items = [
            "1. shaders – CAB-1dc8d26be8722a766953ce9d8a444e8c",
            "2. fc0001_11 – CAB-c0f842cf440c0c4d1d1fd29ea3e98545",
            "3. pc_parts – CAB-8c17e28870d92cd757f025e34576ea93"
        ]

        self.draggable_button_list = DraggableButtonList(self.drag_frame, items, bg="#333")
        self.draggable_button_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Toggle button
        self.toggle_button = Button(self.drag_frame, text="Change to Dawn", command=self.toggle_texts, bg="#555", fg="white", highlightbackground="#333")
        self.toggle_button.pack(side=tk.BOTTOM, padx=5, pady=5)

        # Frame for the animation paths text box
        self.anim_frame = Frame(self.root, bg="#333")
        self.anim_frame.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # Text widget for displaying animation paths
        self.animations_text = Text(self.anim_frame, height=6, width=80, bg="#444", fg="white", highlightbackground="#333")
        self.animations_text.pack(fill=tk.BOTH, expand=True)

        self.file1_path = None
        self.file2_path = None
        self.smr_details1 = None
        self.smr_details2 = None
        self.env1 = None
        self.env2 = None

        # Configure grid to expand with window resizing
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)  # Equal weight for both columns
        self.root.grid_columnconfigure(1, weight=1)  # Equal weight for both columns
        frame.grid_columnconfigure(1, weight=1)
        self.anim_frame.grid_columnconfigure(0, weight=1)

        # Initial text for animations
        self.animations_text_dawn = """bike_wait_f – assets/chara/fc/fc0002_11_heroine/export/bike_wait_f.anim – -4318756635450957882
bike_walk_f – assets/chara/fc/fc0002_11_heroine/export/bike_walk_f.anim – -8668774734267209846
bike_run_f – assets/chara/fc/fc0002_11_heroine/export/bike_run_f.anim – -2817137972230108894

shader – 6563995300646652156"""
        self.animations_text_lucas = """bike_wait_f – assets/chara/fc/fc0001_11_hero/export/bike_wait_f.anim – -6024941013814940029
bike_walk_f – assets/chara/fc/fc0001_11_hero/export/bike_walk_f.anim – 3994984178582008592
bike_run_f – assets/chara/fc/fc0001_11_hero/export/bike_run_f.anim – -5328614080619467906

shader – 6563995300646652156"""

        self.animations_text.insert(tk.END, self.animations_text_lucas)

    def load_file1(self):
        self.file1_path = filedialog.askopenfilename()
        if self.file1_path:
            self.file1_label.config(text=truncate_path(self.file1_path))
        self.check_files_loaded()

    def load_file2(self):
        self.file2_path = filedialog.askopenfilename()
        if self.file2_path:
            self.file2_label.config(text=truncate_path(self.file2_path))
        self.check_files_loaded()

    def check_files_loaded(self):
        if self.file1_path and self.file2_path:
            self.compare_button.config(state=tk.NORMAL)

    def load_data(self):
        self.env1 = UnityPy.load(self.file1_path)
        self.env2 = UnityPy.load(self.file2_path)

        self.smr_details1 = list_skinned_mesh_renderers(self.file1_path)
        self.smr_details2 = list_skinned_mesh_renderers(self.file2_path)

        self.update_smr_list()

    def update_smr_list(self, *args):
        self.smr_listbox.delete(0, tk.END)
        smr_dict1 = {details[1]: details for details in self.smr_details1}
        smr_dict2 = {details[1]: details for details in self.smr_details2}

        common_names = set(smr_dict1.keys()).intersection(set(smr_dict2.keys()))

        for name in common_names:
            self.smr_listbox.insert(tk.END, name)

    def update_result_text(self, event):
        selection = self.smr_listbox.curselection()
        if not selection:
            return

        selected_name = self.smr_listbox.get(selection[0])
        smr_dict1 = {details[1]: details for details in self.smr_details1}
        smr_dict2 = {details[1]: details for details in self.smr_details2}

        details1 = get_smr_details(self.env1, smr_dict1[selected_name])
        details2 = get_smr_details(self.env2, smr_dict2[selected_name])

        info_type = self.info_type_var.get()

        comparison_result = f"Comparing {details1['go_name']}:\n"
        comparison_result += f"PathID (File 1): {details1['smr_path_id']} vs PathID (File 2): {details2['smr_path_id']}\n"

        if info_type == "Bones":
            comparison_result += f"Root Bone: {details1['root_bone_name']} vs {details2['root_bone_name']}\n"
            comparison_result += "Bones:\n"
            for idx, (_, name1, path_id1), (_, name2, path_id2) in zip(range(len(details1['bone_details'])), details1['bone_details'], details2['bone_details']):
                comparison_result += f"  {idx}. {name1} ({path_id1}) vs {name2} ({path_id2})\n"
        elif info_type == "Materials and Mesh":
            comparison_result += "Materials:\n"
            for idx, (_, path_id1, file_id1), (_, path_id2, file_id2) in zip(range(len(details1['material_details'])), details1['material_details'], details2['material_details']):
                comparison_result += f"  {idx}. {path_id1} (FileID: {file_id1}) vs {path_id2} (FileID: {file_id2})\n"
            comparison_result += f"Mesh:\n  0. {details1['mesh_details'][0]} (FileID: {details1['mesh_details'][1]}) vs {details2['mesh_details'][0]} (FileID: {details2['mesh_details'][1]})\n"

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, comparison_result)

    def toggle_texts(self):
        if self.toggle_button.cget("text") == "Change to Dawn":
            self.toggle_button.config(text="Change to Lucas")
            for button in self.draggable_button_list.buttons:
                if "fc0001_11" in button.cget("text"):
                    button.config(text="2. fc0002_11 - CAB-2663951448d3baf89b0c48ea316aef91")
            self.animations_text.delete(1.0, tk.END)
            self.animations_text.insert(tk.END, self.animations_text_dawn)
        else:
            self.toggle_button.config(text="Change to Dawn")
            for button in self.draggable_button_list.buttons:
                if "fc0002_11" in button.cget("text"):
                    button.config(text="2. fc0001_11 - CAB-c0f842cf440c0c4d1d1fd29ea3e98545")
            self.animations_text.delete(1.0, tk.END)
            self.animations_text.insert(tk.END, self.animations_text_lucas)
        self.draggable_button_list.update_button_texts()

if __name__ == "__main__":
    root = tk.Tk()
    app = PlayerBundleCompareApp(root)
    root.mainloop()
