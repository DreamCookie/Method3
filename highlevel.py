import tkinter as tk
from tkinter import messagebox, ttk
import uuid
import json
import math

class TaskBlock:
    def __init__(self, name, resources, duration, earliest_start=0.0, 
                 deadline=None, dependencies=None, reconfiguration_needed=False):
        self.id = str(uuid.uuid4())
        self.name = name
        self.resources = resources
        self.duration = duration
        self.earliest_start = earliest_start
        self.deadline = deadline
        self.dependencies = dependencies if dependencies else []
        self.reconfiguration_needed = reconfiguration_needed
        
        # Поля, которые будут заполнены после планирования
        self.scheduled_start = None
        self.scheduled_end = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "resources": self.resources,
            "duration": self.duration,
            "earliest_start": self.earliest_start,
            "deadline": self.deadline,
            "dependencies": self.dependencies,
            "reconfiguration_needed": self.reconfiguration_needed,
            "scheduled_start": self.scheduled_start,
            "scheduled_end": self.scheduled_end
        }

class TaskEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Высокоуровневый планировщик (интерфейс оператора)")
        
        # Набор задач (в реальном случае можно читать из JSON при инициализации)
        self.tasks = [
            TaskBlock("LoadMaterialA", ["Robot1", "BufferA"], 5.0),
            TaskBlock("MoveToMachine1", ["Robot1"], 3.0, dependencies=["LoadMaterialA"], reconfiguration_needed=True),
            TaskBlock("ProcessOnMachine1", ["Machine1"], 10.0, dependencies=["MoveToMachine1"]),
        ]
        
        # Фрейм для таблицы
        self.tree = ttk.Treeview(root, columns=("Name", "Duration", "EarliestStart", 
                                               "Deadline", "Resources", "Deps", "Reconf"), 
                                 show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Duration", text="Duration")
        self.tree.heading("EarliestStart", text="EarliestStart")
        self.tree.heading("Deadline", text="Deadline")
        self.tree.heading("Resources", text="Resources")
        self.tree.heading("Deps", text="Dependencies")
        self.tree.heading("Reconf", text="ReconfNeeded")
        
        self.tree.column("Name", width=120)
        self.tree.column("Duration", width=80)
        self.tree.column("EarliestStart", width=100)
        self.tree.column("Deadline", width=80)
        self.tree.column("Resources", width=120)
        self.tree.column("Deps", width=120)
        self.tree.column("Reconf", width=100)
        
        self.tree.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Кнопки
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.btn_add = tk.Button(btn_frame, text="Add Task", command=self.add_task_dialog)
        self.btn_edit = tk.Button(btn_frame, text="Edit Task", command=self.edit_task_dialog)
        self.btn_remove = tk.Button(btn_frame, text="Remove Task", command=self.remove_selected_task)
        self.btn_update_plan = tk.Button(btn_frame, text="Update Plan", command=self.update_plan)
        self.btn_gen_graph = tk.Button(btn_frame, text="Generate Graph", command=self.generate_graph)
        self.btn_compute_schedule = tk.Button(btn_frame, text="Compute Schedule", command=self.compute_schedule)
        self.btn_show_gantt = tk.Button(btn_frame, text="Show Gantt", command=self.show_gantt)
        
        self.btn_add.pack(side=tk.LEFT, padx=5)
        self.btn_edit.pack(side=tk.LEFT, padx=5)
        self.btn_remove.pack(side=tk.LEFT, padx=5)
        self.btn_update_plan.pack(side=tk.LEFT, padx=5)
        self.btn_gen_graph.pack(side=tk.LEFT, padx=5)
        self.btn_compute_schedule.pack(side=tk.LEFT, padx=5)
        self.btn_show_gantt.pack(side=tk.LEFT, padx=5)
        
        self.populate_tree()
        
        # Окно для Гантта - создаём при необходимости
        self.gantt_window = None
    
    def populate_tree(self):
        # Очистить текущее дерево
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Добавить задачи
        for t in self.tasks:
            self.tree.insert("", tk.END, iid=t.id,
                             values=(t.name,
                                     t.duration,
                                     t.earliest_start,
                                     t.deadline if t.deadline is not None else "",
                                     ",".join(t.resources),
                                     ",".join(t.dependencies),
                                     "Yes" if t.reconfiguration_needed else "No"))
    
    def add_task_dialog(self):
        """Диалоговое окно для добавления новой задачи."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Task")
        
        tk.Label(dialog, text="Name:").grid(row=0, column=0, sticky="e")
        name_var = tk.StringVar()
        tk.Entry(dialog, textvariable=name_var).grid(row=0, column=1)
        
        tk.Label(dialog, text="Duration:").grid(row=1, column=0, sticky="e")
        dur_var = tk.StringVar(value="5.0")
        tk.Entry(dialog, textvariable=dur_var).grid(row=1, column=1)
        
        tk.Label(dialog, text="Earliest Start:").grid(row=2, column=0, sticky="e")
        es_var = tk.StringVar(value="0.0")
        tk.Entry(dialog, textvariable=es_var).grid(row=2, column=1)
        
        tk.Label(dialog, text="Deadline:").grid(row=3, column=0, sticky="e")
        dl_var = tk.StringVar(value="")
        tk.Entry(dialog, textvariable=dl_var).grid(row=3, column=1)
        
        tk.Label(dialog, text="Resources (comma-separated):").grid(row=4, column=0, sticky="e")
        res_var = tk.StringVar(value="Robot1")
        tk.Entry(dialog, textvariable=res_var).grid(row=4, column=1)
        
        tk.Label(dialog, text="Dependencies (comma-sep):").grid(row=5, column=0, sticky="e")
        dep_var = tk.StringVar(value="")
        tk.Entry(dialog, textvariable=dep_var).grid(row=5, column=1)
        
        reconf_var = tk.BooleanVar(value=False)
        tk.Checkbutton(dialog, text="Reconfiguration needed", variable=reconf_var).grid(row=6, column=1, sticky="w")
        
        def on_add():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Name cannot be empty!")
                return
            # создать TaskBlock
            try:
                duration = float(dur_var.get())
                earliest_start = float(es_var.get())
                dl = dl_var.get().strip()
                if dl == "":
                    deadline = None
                else:
                    deadline = float(dl)
                resources = [r.strip() for r in res_var.get().split(",") if r.strip()]
                deps = [d.strip() for d in dep_var.get().split(",") if d.strip()]
                
                tb = TaskBlock(name=name,
                               resources=resources,
                               duration=duration,
                               earliest_start=earliest_start,
                               deadline=deadline,
                               dependencies=deps,
                               reconfiguration_needed=reconf_var.get())
                # добавим
                self.tasks.append(tb)
                dialog.destroy()
                self.populate_tree()
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric input!")
        
        tk.Button(dialog, text="Add", command=on_add).grid(row=7, column=0, columnspan=2, pady=10)
    
    def edit_task_dialog(self):
        """Диалоговое окно для редактирования существующей задачи."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Error", "No task selected to edit!")
            return
        selected_id = sel[0]
        task_obj = None
        for t in self.tasks:
            if t.id == selected_id:
                task_obj = t
                break
        if not task_obj:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Task")
        
        # Создаём поля ввода с исходными значениями
        tk.Label(dialog, text="Name:").grid(row=0, column=0, sticky="e")
        name_var = tk.StringVar(value=task_obj.name)
        tk.Entry(dialog, textvariable=name_var).grid(row=0, column=1)
        
        tk.Label(dialog, text="Duration:").grid(row=1, column=0, sticky="e")
        dur_var = tk.StringVar(value=str(task_obj.duration))
        tk.Entry(dialog, textvariable=dur_var).grid(row=1, column=1)
        
        tk.Label(dialog, text="Earliest Start:").grid(row=2, column=0, sticky="e")
        es_var = tk.StringVar(value=str(task_obj.earliest_start))
        tk.Entry(dialog, textvariable=es_var).grid(row=2, column=1)
        
        tk.Label(dialog, text="Deadline:").grid(row=3, column=0, sticky="e")
        dl_val = "" if task_obj.deadline is None else str(task_obj.deadline)
        dl_var = tk.StringVar(value=dl_val)
        tk.Entry(dialog, textvariable=dl_var).grid(row=3, column=1)
        
        tk.Label(dialog, text="Resources (comma-separated):").grid(row=4, column=0, sticky="e")
        res_var = tk.StringVar(value=",".join(task_obj.resources))
        tk.Entry(dialog, textvariable=res_var).grid(row=4, column=1)
        
        tk.Label(dialog, text="Dependencies (comma-sep):").grid(row=5, column=0, sticky="e")
        dep_var = tk.StringVar(value=",".join(task_obj.dependencies))
        tk.Entry(dialog, textvariable=dep_var).grid(row=5, column=1)
        
        reconf_var = tk.BooleanVar(value=task_obj.reconfiguration_needed)
        tk.Checkbutton(dialog, text="Reconfiguration needed", variable=reconf_var).grid(row=6, column=1, sticky="w")
        
        def on_save():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Name cannot be empty!")
                return
            try:
                new_dur = float(dur_var.get())
                new_es = float(es_var.get())
                dl = dl_var.get().strip()
                if dl == "":
                    new_deadline = None
                else:
                    new_deadline = float(dl)
                new_res = [r.strip() for r in res_var.get().split(",") if r.strip()]
                new_deps = [d.strip() for d in dep_var.get().split(",") if d.strip()]
                
                task_obj.name = name
                task_obj.duration = new_dur
                task_obj.earliest_start = new_es
                task_obj.deadline = new_deadline
                task_obj.resources = new_res
                task_obj.dependencies = new_deps
                task_obj.reconfiguration_needed = reconf_var.get()
                
                dialog.destroy()
                self.populate_tree()
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric input!")
        
        tk.Button(dialog, text="Save changes", command=on_save).grid(row=7, column=0, columnspan=2, pady=10)
    
    def remove_selected_task(self):
        sel = self.tree.selection()
        if not sel:
            return
        selected_id = sel[0]
        self.tasks = [t for t in self.tasks if t.id != selected_id]
        self.populate_tree()
        
    def update_plan(self):
        """
        Экспортирует базовый список задач (без структуры «рёбер») в editedHighLevelPlan.json.
        """
        tasks_dict = [t.to_dict() for t in self.tasks]
        with open("editedHighLevelPlan.json", "w", encoding='utf-8') as f:
            json.dump(tasks_dict, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Update Plan", "Updated plan exported to editedHighLevelPlan.json!")
    
    def generate_graph(self):
        """
        Генерация ориентированного графа (adjacency list) на основе зависимостей.
        Проверка на наличие циклов. Если циклов нет, граф экспортируется в highLevelPlanGraph.json.
        """
        # Строим словарь: id -> TaskBlock
        task_map = {t.id: t for t in self.tasks}
        
        # adjacency: {taskId: [listOfNextTasksIds]}
        adjacency = {}
        for t in self.tasks:
            adjacency[t.id] = []
        
        # Заполняем adjacency из dependencies
        for t in self.tasks:
            for dep_name in t.dependencies:
                # Найдём задачу с таким name
                dep_candidates = [x for x in self.tasks if x.name == dep_name]
                if len(dep_candidates) == 1:
                    dep_id = dep_candidates[0].id
                    adjacency[dep_id].append(t.id)
                elif len(dep_candidates) > 1:
                    # неоднозначное имя
                    pass
                else:
                    # нет такой задачи
                    pass
        
        # Проверка циклов
        visited = set()
        stack = set()
        
        def dfs_cycle_detect(node):
            visited.add(node)
            stack.add(node)
            for nxt in adjacency[node]:
                if nxt not in visited:
                    if dfs_cycle_detect(nxt):
                        return True
                elif nxt in stack:
                    return True
            stack.remove(node)
            return False
        
        has_cycle = False
        for tid in adjacency:
            if tid not in visited:
                if dfs_cycle_detect(tid):
                    has_cycle = True
                    break
        
        if has_cycle:
            messagebox.showwarning("Graph Generation", 
                                   "Невозможно распланировать - возможно циклические зависимости.")
            return
        
        # Формируем структуру данных
        graph_export = {
            "nodes": [],
            "edges": []
        }
        for t in self.tasks:
            graph_export["nodes"].append({
                "id": t.id,
                "name": t.name,
                "duration": t.duration,
                "earliest_start": t.earliest_start,
                "deadline": t.deadline,
                "resources": t.resources,
                "reconfiguration_needed": t.reconfiguration_needed
            })
        for src, nxts in adjacency.items():
            for dst in nxts:
                graph_export["edges"].append({
                    "from": src,
                    "to": dst
                })
        
        out_filename = "highLevelPlanGraph.json"
        with open(out_filename, "w", encoding='utf-8') as f:
            json.dump(graph_export, f, indent=2, ensure_ascii=False)
        
        messagebox.showinfo("Graph Generation", 
                            f"Graph generated and exported to {out_filename}!")
    
    def compute_schedule(self):
        """
        Упрощённое планирование:
        1) Выполняем топологическую сортировку
        2) Для каждого узла в порядке сортировки находим время старта:
           start_i = max(earliest_start_i, max(end_of_deps))
           end_i = start_i + duration
        3) Проверяем deadline, если end_i > deadline -> предупреждение
        4) Сохраняем результат в planScheduled.json
        """
        # Сформируем adjacency
        adjacency = {}
        name_to_task = {}
        for t in self.tasks:
            adjacency[t.id] = []
            name_to_task[t.name] = t  # для быстрого поиска по имени
        
        # Заполняем adjacency
        id_map = {t.name: t.id for t in self.tasks}
        for t in self.tasks:
            for dname in t.dependencies:
                if dname in id_map:
                    adjacency[id_map[dname]].append(t.id)
        
        # Топологическая сортировка
        visited = set()
        temp_mark = set()
        result = []
        
        def dfs_topo(u):
            if u in temp_mark:
                # цикл
                raise ValueError("Detected cycle during scheduling")
            if u not in visited:
                temp_mark.add(u)
                for nxt in adjacency[u]:
                    dfs_topo(nxt)
                temp_mark.remove(u)
                visited.add(u)
                result.insert(0, u)
        
        # Запустить dfs для всех
        for t in self.tasks:
            if t.id not in visited:
                try:
                    dfs_topo(t.id)
                except ValueError:
                    messagebox.showerror("Compute Schedule", "Cycle detected, can't schedule.")
                    return
        
        # Теперь result содержит список id задач в топологическом порядке
        # Вычислим start/end
        id_to_task = {t.id: t for t in self.tasks}
        
        for tid in result:
            task_obj = id_to_task[tid]
            # вычисляем end_of_deps
            max_dep_end = 0.0
            for dname in task_obj.dependencies:
                # находим id, берем end
                dep_candidates = [x for x in self.tasks if x.name == dname]
                if len(dep_candidates) == 1:
                    dep_t = dep_candidates[0]
                    if dep_t.scheduled_end is not None:
                        if dep_t.scheduled_end > max_dep_end:
                            max_dep_end = dep_t.scheduled_end
            start_time = max(task_obj.earliest_start, max_dep_end)
            end_time = start_time + task_obj.duration
            # проверка deadline
            if task_obj.deadline is not None:
                if end_time > task_obj.deadline:
                    # Примитивная реакция: вывести предупреждение
                    print(f"Task {task_obj.name} surpasses its deadline.")
            task_obj.scheduled_start = start_time
            task_obj.scheduled_end = end_time
        
        # Сохранить результат
        outdata = []
        for t in self.tasks:
            outdata.append(t.to_dict())
        
        with open("planScheduled.json", "w", encoding='utf-8') as f:
            json.dump(outdata, f, indent=2, ensure_ascii=False)
        
        messagebox.showinfo("Compute Schedule", "Plan computed and saved to planScheduled.json")
    
    def show_gantt(self):
        """
        Простая визуализация расписания (scheduled_start, scheduled_end)
        """
        # Проверим, есть ли planScheduled.json
        # Но можно брать из self.tasks
        # Просто возьмём self.tasks, если scheduled_start нет, то предупредить
        any_scheduled = any(t.scheduled_start is not None for t in self.tasks)
        if not any_scheduled:
            messagebox.showinfo("Show Gantt", "No scheduling info. Please compute schedule first!")
            return
        
        if self.gantt_window is not None:
            self.gantt_window.destroy()
        self.gantt_window = tk.Toplevel(self.root)
        self.gantt_window.title("Gantt Chart")
        
        canvas = tk.Canvas(self.gantt_window, width=800, height=400, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # найдем min_start и max_end
        min_start = min(t.scheduled_start for t in self.tasks if t.scheduled_start is not None)
        max_end = max(t.scheduled_end for t in self.tasks if t.scheduled_end is not None)
        if min_start is None or max_end is None:
            messagebox.showinfo("Show Gantt", "No valid schedule.")
            return
        
        time_range = max_end - min_start
        if time_range <= 0:
            time_range = 1.0
        
        # вертикальный шаг
        row_height = 30
        top_margin = 20
        left_margin = 50
        
        sorted_tasks = sorted(self.tasks, key=lambda x: x.scheduled_start if x.scheduled_start else 0)
        
        # ось времени
        # нарисуем шкалу
        scale_width = 700
        scale_height = 20
        canvas.create_line(left_margin, top_margin, left_margin + scale_width, top_margin, fill="black", width=2)
        # некоторые метки по оси
        tick_count = 10
        for i in range(tick_count+1):
            frac = i / tick_count
            t_val = min_start + frac * time_range
            x_pos = left_margin + frac * scale_width
            canvas.create_line(x_pos, top_margin-5, x_pos, top_margin+5, fill="black")
            canvas.create_text(x_pos, top_margin+10, text=f"{t_val:.1f}", anchor="n", font=("Arial",8))
        
        # теперь рисуем прямоугольники
        y_offset = top_margin + scale_height + 10
        for idx, t in enumerate(sorted_tasks):
            # если нет scheduled_start
            if t.scheduled_start is None or t.scheduled_end is None:
                continue
            startf = t.scheduled_start
            endf = t.scheduled_end
            frac_start = (startf - min_start)/time_range
            frac_end = (endf - min_start)/time_range
            
            x1 = left_margin + frac_start * scale_width
            x2 = left_margin + frac_end * scale_width
            y1 = y_offset + idx*row_height
            y2 = y1 + row_height*0.8
            
            # draw rect
            color = "#%02x%02x%02x" % (int(100+idx*25)%200, int(200-idx*15)%200, int(50+idx*45)%200)
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
            canvas.create_text(x1+5, y1+10, text=f"{t.name}", anchor="w", font=("Arial",9,"bold"))
        
        canvas.config(scrollregion=canvas.bbox("all"))

if __name__ == "__main__":
    root = tk.Tk()
    gui = TaskEditorGUI(root)
    root.mainloop()
