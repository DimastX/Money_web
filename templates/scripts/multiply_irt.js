// Функция для перемножения двух чисел из полей ввода и отображения результата.
// Примечание: в текущей реализации аргументы функции num1, num2, result не используются,
// а переменные num1, num2 и result переопределяются внутри функции, что является ошибкой.
// Аргумент result также конфликтует с вычисляемой переменной result. Вроде не используется.
function updateResult(num1, num2, result) {
    // Получение ссылок на HTML-элементы по их ID.
    const num1Input = document.getElementById("num1");
    const num2Input = document.getElementById("num2");
    const resultSpan = document.getElementById("result");

    // Извлечение и преобразование значений из полей ввода в числа.
    // Ошибка: переопределение аргумента num1.
    const num1 = parseFloat(num1Input.value);
    // Ошибка: переопределение аргумента num2.
    const num2 = parseFloat(num2Input.value);
    // Вычисление произведения.
    // Ошибка: переопределение аргумента result.
    const result = num1 * num2;
    // Отображение результата в соответствующем HTML-элементе.
    resultSpan.textContent = result;
  }
