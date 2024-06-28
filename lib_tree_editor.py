import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from prettytable import PrettyTable
import lib_sanitizer as Df
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from lib_branch import load_tree, save_tree
import os

class TreeEditor:
    def __init__(self, sync):
        print("-> Tree Editor (Open)")
        self.sync = sync
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.tree = ttk.Treeview(self.root)
        self.tree.pack(side='left', fill='both', expand=True)

        # JSON 데이터를 트리뷰에 삽입
        json_tree = load_tree()
        self.insert_node('', json_tree)

        # 버튼 추가
        add_button = tk.Button(self.root, text="Add Folder", command=self.add_folder)
        add_button.pack(side='top')

        delete_button = tk.Button(self.root, text="Delete Folder", command=self.delete_folder)
        delete_button.pack(side='top')

        self.tree.bind('<<TreeviewSelect>>', self.on_node_select)
        self.root.mainloop()

    def tree_to_json(self, tree, parent=""):
        node_dict = {}
        for child_id in tree.get_children(parent):
            node_text = tree.item(child_id, 'text')
            node_dict[node_text] = self.tree_to_json(tree, child_id)
        return node_dict

    def insert_node(self, parent, element):
        if isinstance(element, dict):
            for key, value in element.items():
                node = self.tree.insert(parent, 'end', text=key, open=False)
                self.insert_node(node, value)

    # 현재 노드에 새로운 자식 노드 추가
    def add_folder(self):
        selected_item = self.tree.selection()
        if selected_item:
            new_folder_name = simpledialog.askstring("New Folder", "Enter the name of the new folder:")
            if new_folder_name:
                self.tree.insert(selected_item[0], 'end', text=new_folder_name, open=False)
                json_new_tree = self.tree_to_json(self.tree, '')
                save_tree(json_new_tree)
                self.sync()

    # 노드 삭제
    def delete_folder(self):
        selected_item = self.tree.selection()
        selected_branch = self.get_node_path(selected_item[0])
        branch_list = selected_branch.split('/')
        file_names = []
        deletion_table = PrettyTable()
        deletion_table.field_names = ['DATE', 'BRANCH', 'CASH_FLOW', 'DESCRIPTION']
        for file_name in os.listdir('transactions'):
            if selected_branch == '':
                file_names.append(file_name)
            else:
                try:
                    _date, _branch, _cashflow, _content = file_name.split('.')[0].split('_')
                    file_branch = _branch.split('-')[1::]
                    if len(file_branch) >= len(branch_list):
                        if branch_list == file_branch[:len(branch_list):]:
                            file_names.append(file_name)
                            row = [_date, _branch.replace('-', '/'), Df.format_cost(int(_cashflow)), _content]
                            deletion_table.add_row(row)
                except Exception as e:
                    print(e)
                    pass

        print("<<Deletion List>>")
        question = f"Do you really delete 'Home/{selected_branch}'?"
        if len(file_names):
            question += f'(\n{len(file_names)} files will be deleted..)'

        if messagebox.askokcancel("Quit", question):
            if selected_item:
                # 루트 노드가 아닐 경우에만 삭제 가능

                if self.tree.parent(selected_item[0]) != '':
                    self.tree.delete(selected_item[0])
                    json_new_tree = self.tree_to_json(self.tree, '')
                    if file_names:
                        for file_name in file_names:
                            try:
                                os.remove(f'transactions/{file_name}')
                            except:
                                pass
                        print(f'\n{len(file_names)} files has been deleted..')

                    save_tree(json_new_tree)
                    self.sync()
                else:
                    messagebox.showinfo("Info", "Root node cannot be deleted.")

    def on_node_select(self, event):
        # 선택된 노드의 경로를 구성
        selected_item = self.tree.selection()
        if selected_item:
            node_path = self.get_node_path(selected_item[0])
            self.root.clipboard_clear()
            self.root.clipboard_append(node_path)

            message = f"-> Path '{node_path}' copied to clipboard."
            print(message)

            # messagebox.showinfo("Node Path", f"Path '{node_path}' copied to clipboard.")

    def get_node_path(self, item_id):
        path = []
        while item_id:
            node = self.tree.item(item_id, 'text')
            path.append(node)
            item_id = self.tree.parent(item_id)

        return '/'.join(path[::-1][1::])

    def on_close(self):
        if messagebox.askokcancel("Quit", "Do you really wish to quit?"):
            self.root.destroy()
            print("-> Tree Editor (Close)")
