"""Реализация простого алгоритма управления движением лифта.
На каждом этаже для вызова лифта предусмотрены две кнопки со стрелками (вверх и вниз).
Правила:
- Пока внутри лифта или на этажах по ходу движения есть пассажиры,
  которым нужно ехать в ту же сторону, лифт движется в эту сторону;
- Если вызовов по ходу движения больше нет, но есть в обратную сторону, лифт меняет направление.
Алгоритм оптимален при небольшом количестве этажей и наличии одного лифта в здании.
"""

from threading import Thread
import time
import random

directions = {1: 'Up', -1: 'Down'}


class Elevator:
    """Класс для управления лифтом.
    Исходное состояние лифта - на уровне 1-го этажа."""

    moving = False
    cur_floor = 1
    speed = 0

    def __init__(self, n_floors):
        """При инициализации экземпляра класса указывается количество этажей в здании.
        В исходном состоянии ни одна из кнопок внутри кабины и на этажах не нажата."""
        self.n_floors = n_floors
        self.inside_buttons = [False for _ in range(n_floors + 1)]
        self.outside_buttons_up = [False for _ in range(n_floors + 1)]
        self.outside_buttons_down = [False for _ in range(n_floors + 1)]

    def press_inside_button(self, floor):
        """Функция обрабатывает нажатие кнопок внутри кабины лифта."""
        print(f'Button {floor} pressed inside the cabin.')

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
        print(f'Button {directions[speed]} on floor {floor} pressed.')

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
            print('Started moving.')
            self.manage_movement()

    def check_status(self, speed):
        """Функция обновляет скорость (направление) движения лифта."""
        if self.speed == 0:
            self.speed = speed

    def manage_movement(self):
        """Функция управляет остановками и открытием дверей при движении лифта."""
        while self.moving:
            print(f'Floor: {self.cur_floor}')

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

        if stop_movement:
            self.stop()
        else:
            self.move()

    def move(self):
        """Функция перемещает лифт на следующий этаж по ходу движения.
        Скорость движения лифта - 1 этаж в секунду."""
        time.sleep(1)
        self.cur_floor += self.speed

    def stop(self):
        """Функция остановливает движение лифта при отсутствии вызовов."""
        self.speed = 0
        self.moving = False
        print('Stopped moving. No buttons pressed.')

    def activate_doors(self):
        """Функция для открытия и закрытия дверей при остановке лифта на этаже.
        Продолжительность остановки - 5 секунд."""
        print('Movement paused.')
        print('Doors opened.')
        time.sleep(5)
        print('Doors closed.')


def random_calls(n_floors):
    """Функция имитирует вызовы лифта пассажирами.
    Нажатие случайной кнопки происходит каждые 3-5 секунд."""
    print('Random function started.')
    global lift

    while True:
        time_gap = random.randint(3, 5)
        time.sleep(time_gap)

        action_type = random.choice(['inside', 'outside'])
        floor = random.randint(1, n_floors)
        if action_type == 'inside':
            Thread(target=lift.press_inside_button, args=(floor,)).start()
        elif action_type == 'outside':
            direction = random.choice([1, -1])
            Thread(target=lift.press_outside_button, args=(floor, direction)).start()


n_floors = int(input('Number of floors:\t'))
lift = Elevator(n_floors)

Thread(target=random_calls, args=(n_floors,)).start()
