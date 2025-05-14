// Функция для управления состоянием (включено/выключено) зависимого элемента
// на основе состояния чекбокса-переключателя.
// ПРИМЕЧАНИЕ: Эта функция является полным дубликатом функции check 
// из файла templates/scripts/Checks.js.
function check(master, slave) {
  // Проверка, отмечен ли чекбокс-переключатель (master).
  if (document.getElementById(master).checked) {
    // Если чекбокс отмечен, удаляем класс 'disable_section' у зависимого элемента (slave).
    // Это, вероятно, делает элемент активным или видимым.
    document.getElementById(slave).classList.remove('disable_section')
  } else {
    // Если чекбокс не отмечен, добавляем класс 'disable_section' к зависимому элементу.
    // Это, вероятно, делает элемент неактивным или скрытым.
    document.getElementById(slave).classList.add('disable_section')
  }
}