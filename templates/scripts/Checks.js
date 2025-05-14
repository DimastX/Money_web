// Функция для управления состоянием (включено/выключено) зависимого элемента
// на основе состояния чекбокса-переключателя.
function check(master_box, slave) {
    // Проверка, отмечен ли чекбокс-переключатель (master_box).
    if (document.getElementById(master_box).checked) {
      // Если чекбокс отмечен, удаляем класс 'disable_section' у зависимого элемента (slave).
      // Это, вероятно, делает элемент активным или видимым.
      document.getElementById(slave).classList.remove('disable_section')
    } else {
      // Если чекбокс не отмечен, добавляем класс 'disable_section' к зависимому элементу.
      // Это, вероятно, делает элемент неактивным или скрытым.
      document.getElementById(slave).classList.add('disable_section')
    }
  }