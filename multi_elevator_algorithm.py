"""Реализация простого алгоритма с синхронизацией работы нескольких лифтов.
При запуске скрипта задается количество этажей в здании и количество лифтов.
На каждом этаже для вызова лифта предусмотрены две кнопки со стрелками (вверх и вниз).
Нажатие кнопок в кабинах лифтов и на этажах имитируют функции со случайным выбором.
Для синхронизации работы лифтов используется дополнительный класс, отслеживающий
положение и направление движения лифтов и формирующий приоритетную очередь.
Правила движения лифтов:
- При прочих равных условиях на новый вызов с этажа приезжает ближайший к нему лифт.
- Для каждого отдельного лифта - пока внутри лифта или на этажах по ходу движения
  есть пассажиры, которым нужно ехать в ту же сторону и чьи вызовы были адресованы
  этому лифту, лифт движется в эту сторону.
- Если вызовов по ходу движения больше нет, но есть в обратную сторону, лифт меняет направление.
Алгоритм оптимален при небольшом количестве этажей в здании.
"""

from threading import Thread
from queue import PriorityQueue
import time
import random

n_floors = int(input('Number of floors:\t'))
n_elevators = int(input('Number of elevators:\t'))

directions = {1: 'Up', -1: 'Down'}


class Dispatcher:
    """Класс для синхронизации работы нескольких лифтов."""

    # id лифта соответствует позиции элемента в списках:
    elevators_position = []  # Текущий этаж
    elevators_speed = []  # Скорость и направление движения

    def add_object(self):
        """Функция добавляет сведения о новом лифте в систему синхронизации."""
        self.elevators_position.append(1)
        self.elevators_speed.append(0)

    def update_object_position(self, obj_id, pos):
        """Функция обновляет данные об этаже расположения лифта."""
        self.elevators_position[obj_id] = pos

    def update_object_speed(self, obj_id, speed):
        """Функция обновляет данные о направлении движения лифта."""
        self.elevators_speed[obj_id] = speed

    def press_outside_button(self, floor, speed):
        """Функция обрабатывает нажатие кнопки вызора лифта с этажа:
        находит ближайший к месту вызова лифт и переадресует ему вызов."""
        queue = PriorityQueue(maxsize=n_elevators)  # Очередь расстояний до всех лифтов
        distance_to_id = dict()  # Ключи - расстояния, значения - id лифтов
        for obj_id in range(n_elevators):
            distance = self.distance(obj_id, floor, speed)
            queue.put(distance)
            distance_to_id[distance] = obj_id
        shortest_distance = queue.get()
        nearest_elevator = distance_to_id[shortest_distance]
        elevators_list[nearest_elevator].press_outside_button(floor, speed)

    def distance(self, obj_id, call_floor, call_speed):
        """Функция находит расстояние от лифта до этажа, с которого поступил вызов."""
        pos = self.elevators_position[obj_id]
        speed = self.elevators_speed[obj_id]

        if speed == 0:  # Лифт стоит
            return abs(call_floor - pos)

        # Лифт движется в том же направлении, что и поступивший вызов
        if speed == call_speed:
            if speed == 1:
                if call_floor >= pos:  # Вверх по направлению к этажу вызова
                    return call_floor - pos
                else:  # Уже проехал мимо. В худшем случае лифт доедет до конца, развернется
                    # и снова может доехать до конца, а уже потом вернется к нужному этажу.
                    return 2 * n_floors - pos + call_floor
            elif speed == -1:
                if call_floor <= pos:  # Вниз по направлению к этажу вызова
                    return pos - call_floor
                else:  # Уже проехал мимо
                    return pos + 2 * n_floors - call_floor

        # Лифт движется в противоположном направлении. В худшем случае он доедет
        # до последнего в этом направлении этажа и потом вернется к нужному этажу.
        else:
            if speed == 1:
                return n_floors - pos + abs(call_floor - pos)
            else:  # speed = -1
                return pos + abs(call_floor - pos)


class Elevator:
    """Класс для управления лифтом."""

    n_elevators = 0  # Счетчик количества экземпляров класса,
    # служит для присваивания id новым экземплярам класса.

    def __init__(self, n_floors):
        """При инициализации экземпляра класса указывается количество этажей в здании.
        Исходное состояние лифта - на уровне 1-го этажа, ни одна из кнопок не нажата."""
        self.n_floors = n_floors
        self.moving = False
        self.cur_floor = 1
        self.speed = 0
        self.inside_buttons = [False for _ in range(n_floors + 1)]
        self.outside_buttons_up = [False for _ in range(n_floors + 1)]
        self.outside_buttons_down = [False for _ in range(n_floors + 1)]
        self.id = Elevator.n_elevators
        Elevator.n_elevators += 1
        dispatcher.add_object()  # Синхронизация лифтов для распределения вызовов с этажей
        print(f'Elevator object with id={self.id} created.')
        print(f'Total number of elevators = {self.n_elevators}')

    def press_inside_button(self, floor):
        """Функция обрабатывает нажатие кнопок внутри кабины лифта."""
        print(f'Elevator {self.id}: button {floor} pressed inside the cabin.')
        self.inside_buttons[floor] = True

        delta = floor - self.cur_floor
        if delta > 0:
            speed = 1
        elif delta < 0:
            speed = -1
        else:
            speed = 0

        self.check_status(speed)
        self.start_moving()

    def press_outside_button(self, floor, speed):
        """Функция обрабатывает нажатие кнопок на этажах."""
        print(f'Elevator {self.id}: button {directions[speed]} on floor {floor} pressed.')

        if speed == 1:
            self.outside_buttons_up[floor] = True
        elif speed == -1:
            self.outside_buttons_down[floor] = True

        self.check_status(speed)
        self.start_moving()

    def start_moving(self):
        """Функция приводит лифт в движение."""
        if not self.moving:
            self.moving = True
            print(f'Elevator {self.id} started moving.')
            self.manage_movement()

    def check_status(self, speed):
        """Функция обновляет скорость (направление) движения
        только для стоящего лифта."""
        if self.speed == 0:
            self.speed = speed
            dispatcher.update_object_speed(self.id, self.speed)

    def manage_movement(self):
        """Функция управляет остановками и открытием дверей при движении лифта."""
        while self.moving:
            print(f'Elevator {self.id} on floor {self.cur_floor}')

            # Если внутри кабины нажата кнопка текущего этажа:
            if self.inside_buttons[self.cur_floor]:
                self.activate_doors()
                self.inside_buttons[self.cur_floor] = False
            # Если на текущем этаже нажата кнопка "Вверх" при движении лифта наверх:
            elif self.speed == 1 and self.outside_buttons_up[self.cur_floor]:
                self.activate_doors()
                self.outside_buttons_up[self.cur_floor] = False
            # Если на текущем этаже нажата кнопка "Вниз" при движении лифта вниз:
            elif self.speed == -1 and self.outside_buttons_down[self.cur_floor]:
                self.activate_doors()
                self.outside_buttons_down[self.cur_floor] = False
            # Стоявший лифт вызван с этажа для движения в противоположном направлении:
            elif sum(self.inside_buttons) == 0:
                if sum(self.outside_buttons_up) == 0 and self.outside_buttons_down[self.cur_floor]:
                    self.activate_doors()
                    self.outside_buttons_down[self.cur_floor] = False
                elif sum(self.outside_buttons_down) == 0 and self.outside_buttons_up[self.cur_floor]:
                    self.activate_doors()
                    self.outside_buttons_up[self.cur_floor] = False

            self.check_buttons()

    def check_buttons(self):
        """Функция проверяет состояние всех кнопок в кабине и на этажах,
        изменяет скорость (направление) движения и позицию лифта."""

        inside_higher = sum(self.inside_buttons[self.cur_floor+1:])
        inside_lower = sum(self.inside_buttons[:self.cur_floor])

        outside_higher_up = sum(self.outside_buttons_up[self.cur_floor+1:])
        outside_lower_up = sum(self.outside_buttons_up[:self.cur_floor])
        outside_higher_down = sum(self.outside_buttons_down[self.cur_floor+1:])
        outside_lower_down = sum(self.outside_buttons_down[:self.cur_floor])

        # Проверка кнопок при движении вверх:
        if self.speed == 1:
            # Кнопки по ходу движения вверх в порядке приоритетности:
            if inside_higher > 0 or outside_higher_up > 0 or outside_higher_down > 0:
                stop_movement = False
            # Кнопки ниже текущего этажа в любом направлении:
            elif inside_lower > 0 or outside_lower_up > 0 or outside_lower_down > 0:
                self.speed = -1
                stop_movement = False
            else:  # Нет нажатых кнопок:
                stop_movement = True

        # Проверка кнопок при движении вниз:
        elif self.speed == -1:
            # Кнопки по ходу движения вниз в порядке приоритетности:
            if inside_lower > 0 or outside_lower_down > 0 or outside_lower_up > 0:
                stop_movement = False
            # Кнопки выше текущего этажа в любом направлении:
            elif inside_higher > 0 or outside_higher_up > 0 or outside_higher_down > 0:
                self.speed = 1
                stop_movement = False
            else:  # Нет нажатых кнопок:
                stop_movement = True

        # Случай, когда повторно нажата кнопка текущего этажа после остановки лифта:
        else:
            stop_movement = False  # Лифт с нулевой скоростью останется на том же этаже, но двери откроются.

        if stop_movement:
            self.stop()
        else:
            self.move()

    def move(self):
        """Функция перемещает лифт на следующий этаж по ходу движения.
        Скорость движения лифта - 1 этаж в секунду."""
        time.sleep(1)
        self.cur_floor += self.speed
        dispatcher.update_object_position(self.id, self.cur_floor)

    def stop(self):
        """Функция остановливает движение лифта при отсутствии вызовов."""
        self.speed = 0
        self.moving = False
        dispatcher.update_object_speed(self.id, self.speed)
        print(f'Elevator {self.id} stopped moving. No buttons pressed.')

    def activate_doors(self):
        """Функция для открытия и закрытия дверей при остановке лифта на этаже.
        Продолжительность остановки - 5 секунд."""
        print(f'Elevator {self.id}: movement paused.')
        print(f'Elevator {self.id}: doors opened.')
        time.sleep(5)
        print(f'Elevator {self.id}: doors closed.')


def random_inside_calls(n_floors):
    """Функция имитирует нажатие кнопок в кабинах лифтов пассажирами.
    Нажатие случайной кнопки происходит каждые 2-3 секунды."""
    print('Random function for buttons inside cabins started.')
    while True:
        time_gap = random.randint(2, 3)
        time.sleep(time_gap)
        elevator = random.randint(0, n_elevators - 1)
        floor = random.randint(1, n_floors)
        Thread(target=elevators_list[elevator].press_inside_button, args=(floor,)).start()


def random_outside_calls(n_floors):
    """Функция имитирует нажатие кнопок вызова лифта пассажирами на этажах.
    Нажатие случайной кнопки происходит каждые 2-3 секунды."""
    print('Random function for outside buttons started.')
    while True:
        time_gap = random.randint(2, 3)
        time.sleep(time_gap)
        floor = random.randint(1, n_floors)
        if floor == 1:
            direction = 1
        elif floor == n_floors:
            direction = -1
        else:
            direction = random.choice([1, -1])
        Thread(target=dispatcher.press_outside_button, args=(floor, direction)).start()


# Синхронизация работы лифтов:
dispatcher = Dispatcher()

# Инициализация указанного количества лифтов:
elevators_list = []
for _ in range(n_elevators):
    elevators_list.append(Elevator(n_floors))

# Генерация нажатий кнопок внутри кабины всех лифтов:
Thread(target=random_inside_calls, args=(n_floors,)).start()

# Генерация нажатий кнопок на этажах:
Thread(target=random_outside_calls, args=(n_floors,)).start()
