import json
import math
import time
import uuid
import random

class VoxelSpace:
    """
    Упрощённый класс, иллюстрирующий воксельное представление окружающего пространства.
    Допустим, что внутри есть метод update_from_sensors(),
    который периодически обновляет информацию о доступных ячейках (voxels),
    учитывая новые данные от системы машинного зрения или датчиков.
    """
    def __init__(self):
        # Для демонстрации храним лишь список занятых/свободных ячеек (dummy)
        self.occupied_voxels = set()  # Например, ("x,y,z")
    
    def update_from_sensors(self):
        # Имитируем периодическое обновление
        # (В реальности: считываем из лидара/камеры/vision-системы)
        # Для демонстрации случайно очищаем или заполняем часть ячеек
        pass
    
    def is_free(self, voxel_id):
        return voxel_id not in self.occupied_voxels
    
    def mark_occupied(self, voxel_id):
        self.occupied_voxels.add(voxel_id)
    
    def mark_free(self, voxel_id):
        if voxel_id in self.occupied_voxels:
            self.occupied_voxels.remove(voxel_id)


class AStarTimeAware:
    """
    Упрощённый алгоритм A* с учётом временных меток.
    Предполагается, что нам доступен граф свободного пространства (например, voxels)
    + информация о времени доступности.
    """
    def __init__(self, voxel_space):
        self.voxel_space = voxel_space
    
    def heuristic(self, nodeA, nodeB):
        # Простая евклидова метрика
        # node: (x, y, z, time?), для упрощения считаем (x, y, z)
        (xA, yA, zA) = nodeA
        (xB, yB, zB) = nodeB
        return math.sqrt((xA - xB)**2 + (yA - yB)**2 + (zA - zB)**2)
    
    def cost_transition(self, nodeA, nodeB):
        """
        Стоимость перехода: дистанция / скорость = время + проверка доступности.
        Для упрощения считаем скорость константой, а доступность берём из
        self.voxel_space.is_free(...)
        """
        hval = self.heuristic(nodeA, nodeB)
        speed = 1.0  # условная скорость робота
        return hval / speed
    
    def find_path(self, start, goal, start_time, node_availability):
        """
        node_availability[node] = момент времени, когда этот узел доступен
        Если робот приходит раньше, то приходится ждать
        """
        openSet = []
        cameFrom = {}
        
        gScore = {}
        fScore = {}
        
        openSet.append(start)
        gScore[start] = 0.0
        fScore[start] = self.heuristic(start, goal)
        
        while len(openSet) > 0:
            current = min(openSet, key=lambda n: fScore.get(n, float('inf')))
            if current == goal:
                return self.reconstruct_path(cameFrom, current)
            
            openSet.remove(current)
            for neighbor in self.get_neighbors(current):
                if not self.voxel_space.is_free(neighbor):
                    continue
                
                tentative_g = gScore[current] + self.cost_transition(current, neighbor)
                
                # учёт доступности:
                arrival_time = start_time + tentative_g
                # если arrival_time < node_availability[neighbor], значит придётся ждать
                if neighbor in node_availability:
                    if arrival_time < node_availability[neighbor]:
                        # ждем
                        wait_delta = node_availability[neighbor] - arrival_time
                        tentative_g += wait_delta
                
                if neighbor not in gScore or tentative_g < gScore[neighbor]:
                    cameFrom[neighbor] = current
                    gScore[neighbor] = tentative_g
                    fScore[neighbor] = tentative_g + self.heuristic(neighbor, goal)
                    if neighbor not in openSet:
                        openSet.append(neighbor)
        
        return None  # path not found
    
    def get_neighbors(self, node):
        """
        Считаем, что соседи - это +/-1 по каждой координате,
        если не выходят за границы. В реальном решении учитываем
        сложные правила (включая уровни уточнения, etc).
        """
        (x, y, z) = node
        result = []
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                for dz in [-1,0,1]:
                    if abs(dx)+abs(dy)+abs(dz) == 1:
                        nx, ny, nz = x+dx, y+dy, z+dz
                        # упрощённо
                        result.append((nx, ny, nz))
        return result
    
    def reconstruct_path(self, cameFrom, current):
        total_path = [current]
        while current in cameFrom:
            current = cameFrom[current]
            total_path.insert(0, current)
        return total_path


class LowLevelPlanner:
    def __init__(self, voxel_space):
        self.voxel_space = voxel_space
        self.a_star = AStarTimeAware(self.voxel_space)
        self.current_path = []
        self.node_availability = {}  # node->time, время доступности
        
        # Параметры для демонстрации, robot pose:
        self.robot_position = (0,0,0)
        self.current_time = 0.0
        
        # Псевдо-скорость робота, etc
    
    def load_high_level_plan(self, high_level_json_path):
        with open(high_level_json_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        # tasks - это список, содержащий описание задач
        # Для demo считаем, что нас интересует только одна задача - move
        # В реальности: смотреть, какая задача связана с перемещением
        # Возьмём первую задачу, которая требует Robot1
        self.target_node = None
        for t in tasks:
            if "Robot1" in t["resources"]:
                # Примем, что координаты goal - упрощённо, (10,10,0)
                # (в реальности - берем из t?)
                self.target_node = (10,10,0)
                print("Found a movement task for Robot1, assume target is (10,10,0)")
                break
        if not self.target_node:
            print("No movement tasks found for Robot1!")
    
    def update_availability_from_equipment(self, equipment_signals):
        """
        Здесь equipment_signals — словарь, где ключ — это идентификатор узла (x,y,z),
        а значение — момент времени, когда будет свободен/доступен?
        """
        for node, free_time in equipment_signals.items():
            self.node_availability[node] = free_time
    
    def plan_path(self):
        """
        Запуск метода AStarTimeAware, формируем маршрут.
        """
        if not self.target_node:
            print("No target specified.")
            return
        path = self.a_star.find_path(start=self.robot_position,
                                     goal=self.target_node,
                                     start_time=self.current_time,
                                     node_availability=self.node_availability)
        if path is None:
            print("Path not found or blocked!")
            return
        self.current_path = path
        print("Planned path:", path)
    
    def execute_path(self):
        """
        Пошаговое исполнение пути. При каждом шаге проверяем,
        не появилось ли новое препятствие или не стало ли узел недоступен.
        """
        for node in self.current_path[1:]:
            # fake move
            if not self.voxel_space.is_free(node):
                print("Collision detected at node", node, "replanning needed!")
                return  # exit or replan
            # check availability time
            arrival_time = self.current_time + self.a_star.heuristic(self.robot_position, node)
            if node in self.node_availability and arrival_time < self.node_availability[node]:
                wait_t = self.node_availability[node] - arrival_time
                print(f"Waiting {wait_t} units for node {node} to be available...")
                self.current_time += wait_t
            # move
            cost = self.a_star.heuristic(self.robot_position, node)
            # simulate real movement
            time.sleep(0.1)  # fake small delay
            self.current_time += cost
            self.robot_position = node
            print("Moved to", node, "time=", self.current_time)
        print("Path execution done!")
        self.current_path = []
    
    def reactive_cycle(self):
        """
        Основной реактивный цикл:
        - читаем датчики/систему машинного зрения -> voxel_space.update_from_sensors()
        - обновляем доступность узлов
        - проверяем, не надо ли заново перепланировать
        - если да, plan_path()
        - затем execute_path()
        """
        # Упрощённо:
        self.voxel_space.update_from_sensors()
        # возможно, какой-то condition
        # if changed...
        self.plan_path()
        if self.current_path:
            self.execute_path()

if __name__ == "__main__":
    # Имитируем воксельное пространство
    vs = VoxelSpace()

    # Создаём планировщик
    llp = LowLevelPlanner(vs)

    # Загружаем высокоуровневый план
    llp.load_high_level_plan("editedHighLevelPlan.json")

    # Имитируем обновление доступности 
    # (например, где-то машина занята узлами (5,5,0) до времени 10)
    equip_signals = { (5,5,0): 10.0 }
    llp.update_availability_from_equipment(equip_signals)

    # Запустим реактивный цикл один раз (в реальности он был бы в loop)
    llp.reactive_cycle()
